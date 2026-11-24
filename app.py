"""
app.py · THE APP ENGINE (you don't need to edit this file)

Turns a plain-English question into SQL, runs it on your MotherDuck tables,
and shows the answer, the SQL and the rows behind it.

    question ──► Gemini writes SQL ──► guardrails check it ──► MotherDuck runs it
                 (reads your data dictionary)                       │
    answer ◄── Gemini explains the rows ◄───────────────────────────┘

You change the app through app.toml and docs/data_dictionary.md.
Run it in your Codespace with:   streamlit run app.py
"""
import json
import os
import re
import tomllib

import duckdb
import requests
import streamlit as st

DATABASE = "course"   # where pipeline.py publishes: course.main.<table>


# -----------------------------------------------------------------------------
# Settings and secrets
# -----------------------------------------------------------------------------
def read_toml(path):
    try:
        with open(path, "rb") as f:
            return tomllib.load(f)
    except FileNotFoundError:
        return {}
    except tomllib.TOMLDecodeError as e:
        st.error(f"There's a typo in {path}: {e}. Check quotes and brackets on that line.")
        st.stop()


def read_text(path):
    try:
        with open(path, encoding="utf-8") as f:
            text = f.read()
    except FileNotFoundError:
        return ""
    return re.sub(r"<!--.*?-->", "", text, flags=re.S).strip()   # drop template notes


def secret(name):
    """Streamlit Cloud: the Secrets box. Codespace: a Codespaces secret."""
    try:
        if name in st.secrets:
            return str(st.secrets[name]).strip()
    except Exception:
        pass
    return os.environ.get(name, "").strip()


settings = read_toml("app.toml")
project = read_toml("project.toml")
TABLES = [t["name"] for t in project.get("tables", [])]
DICTIONARY = read_text("docs/data_dictionary.md")
MODELS = settings.get("models", ["gemini-3.5-flash-lite", "gemini-3.8-flash"])
MAX_ROWS = int(settings.get("max_rows", 200))


# -----------------------------------------------------------------------------
# MotherDuck: the same tables your pipeline publishes every morning
# -----------------------------------------------------------------------------
@st.cache_resource
def database():
    token = secret("MOTHERDUCK_TOKEN")
    os.environ["motherduck_token"] = token
    return duckdb.connect(f"md:{DATABASE}")


@st.cache_data(ttl=600)
def describe_tables():
    """Column names and types, read live from MotherDuck."""
    out = {}
    for t in TABLES:
        try:
            cols = database().sql(f"DESCRIBE {DATABASE}.main.{t}").fetchall()
            out[t] = [(c[0], c[1]) for c in cols]
        except Exception:
            out[t] = None          # in project.toml but not on MotherDuck yet
    return out


@st.cache_data(ttl=600)
def last_refresh():
    try:
        return database().sql(
            f"SELECT strftime(last_success, '%b %-d, %Y at %-I:%M %p UTC') "
            f"FROM {DATABASE}.main.pipeline_runs").fetchone()[0]
    except Exception:
        return None


# ----------------------------------------------------------------------------
# Gemini: one request in, one answer out
# -----------------------------------------------------------------------------
class AIError(Exception):
    pass


def ask_gemini(prompt, want_json=False):
    key = secret("GEMINI_API_KEY")
    config = {"temperature": 0}
    if want_json:
        config["responseMimeType"] = "application/json"
    last = None
    for model in MODELS:                       # try each model in app.toml, in order
        r = requests.post(
            f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
            headers={"x-goog-api-key": key, "Content-Type": "application/json"},
            json={"contents": [{"parts": [{"text": prompt}]}], "generationConfig": config},
            timeout=60)
        if r.status_code == 200:
            try:
                st.session_state["model_used"] = model
                return r.json()["candidates"][0]["content"]["parts"][0]["text"]
            except (KeyError, IndexError):
                raise AIError("The AI sent back an empty answer. Try rewording the question.")
        if r.status_code == 429:
            raise AIError("The free AI tier is busy: too many questions this minute (or today). "
                          "Wait a minute and ask again.")
        if r.status_code in (400, 401, 403) and "API key" in r.text:
            raise AIError("Gemini didn't accept the key. Check GEMINI_API_KEY in your secrets.")
        last = f"{model}: HTTP {r.status_code}"
        if r.status_code not in (404, 400, 503):   # 404 = that model isn't available: try the next
            break
    raise AIError(f"No AI model answered ({last}). Check the models list in app.toml.")


def schema_text():
    lines = []
    for t, cols in describe_tables().items():
        if cols:
            lines.append(f"{DATABASE}.main.{t}(" + ", ".join(f"{c} {ty}" for c, ty in cols) + ")")
    return "\n".join(lines)


def write_sql(question, error=None):
    prompt = f"""You write DuckDB SQL for a read-only question-answering app.

TABLES (the only tables you may use; always write the full name):
{schema_text()}

DATA DICTIONARY (what the tables and columns mean):
{DICTIONARY or "(none provided)"}

RULES:
- One SELECT statement only (WITH is fine). Never change data.
- Return at most {MAX_ROWS} rows; add ORDER BY so the most useful rows come first.
- Prefer a summary or analysis table when it already holds the answer.
- If these tables can't answer the question, don't guess: set "answerable" to false
  and say in "reason" what data would be needed.
{settings.get("extra_instructions", "").strip()}

QUESTION: {question}
"""
    if error:
        prompt += f"\nYour previous SQL failed with this error. Fix it:\n{error}\n"
    prompt += '\nReply with JSON only: {"answerable": true or false, "sql": "...", "reason": "..."}'
    text = ask_gemini(prompt, want_json=True)
    try:
        return json.loads(text.strip().removeprefix("```json").removesuffix("```"))
    except json.JSONDecodeError:
        raise AIError("The AI's reply wasn't in the expected format. Try asking again.")


def explain(question, sql, df):
    rows = df.head(50).to_csv(index=False) if len(df) else "(no rows)"
    prompt = f"""Answer the question in 1 to 3 plain-English sentences for a non-technical reader,
using ONLY the rows below. Include the key numbers. If there are no rows, say no matching data
was found. Don't mention SQL.

QUESTION: {question}
ROWS ({len(df)} total, first 50 shown):
{rows}"""
    return ask_gemini(prompt).strip()


# -----------------------------------------------------------------------------
# Guardrails: the AI's SQL is checked before it touches your data
# -----------------------------------------------------------------------------
BLOCKED = r"\b(insert|update|delete|drop|create|alter|attach|detach|copy|export|import|install|" \
          r"load|pragma|set|call|truncate|grant|checkpoint|vacuum)\b"
BLOCKED_FUNCTIONS = r"\b(read_\w+|glob|query_table|sniff_csv|getenv)\s*\("


def guard(sql):
    """Returns (safe_sql, None) or (None, the reason it was blocked)."""
    s = (sql or "").strip().rstrip(";").strip()
    no_strings = re.sub(r"'[^']*'", "''", s)           # ignore words inside 'text values'
    if not s:
        return None, "The AI didn't write any SQL."
    if ";" in no_strings:
        return None, "Blocked: more than one statement."
    if not re.match(r"(?is)^\s*(select|with)\b", s):
        return None, "Blocked: only SELECT questions are allowed."
    if re.search(BLOCKED, no_strings, re.I):
        return None, "Blocked: the SQL tried to change or load data."
    if re.search(BLOCKED_FUNCTIONS, no_strings, re.I):
        return None, "Blocked: the SQL tried to read files or settings."
    return f"SELECT * FROM (\n{s}\n) AS answer LIMIT {MAX_ROWS}", None


def run(sql):
    con = database().cursor()
    con.execute("BEGIN TRANSACTION")       # a second safety net: nothing is ever saved
    try:
        return con.sql(sql).df()
    finally:
        con.execute("ROLLBACK")


def answer(question):
    plan = write_sql(question)
    if not plan.get("answerable", True) or not plan.get("sql"):
        return {"question": question, "status": "cannot",
                "text": plan.get("reason") or "This data can't answer that question."}
    for attempt in (1, 2):                 # if the SQL fails, the AI gets one try to fix it
        safe, blocked = guard(plan.get("sql"))
        if blocked:
            return {"question": question, "status": "blocked", "text": blocked, "sql": plan.get("sql")}
        try:
            df = run(safe)
            break
        except duckdb.Error as e:
            if attempt == 2:
                return {"question": question, "status": "error", "sql": plan.get("sql"),
                        "text": f"The SQL didn't run: {str(e).splitlines()[0]}"}
            plan = write_sql(question, error=f"{plan.get('sql')}\n{e}")
    return {"question": question, "status": "ok", "sql": plan["sql"], "rows": df,
            "text": explain(question, plan["sql"], df), "fixed": attempt == 2}


# -----------------------------------------------------------------------------
# The page
# -----------------------------------------------------------------------------
st.set_page_config(page_title=settings.get("title", "Ask the data"), page_icon="💬", layout="centered")
st.title(settings.get("title", "Ask the data"))
if settings.get("description"):
    st.write(settings["description"])

missing = [n for n in ("MOTHERDUCK_TOKEN", "GEMINI_API_KEY") if not secret(n)]
if missing:
    st.error("Missing secret: " + ", ".join(missing) + ". On Streamlit Cloud: share.streamlit.io → "
             "your app's ⋮ → Settings → Secrets. In a Codespace: add it as a Codespaces secret, then restart.")
    st.stop()
if not TABLES:
    st.error("No tables found. app.py reads the [[tables]] list in project.toml.")
    st.stop()

try:
    found = describe_tables()
except Exception as e:
    st.error(f"Couldn't reach MotherDuck: {e}. Check MOTHERDUCK_TOKEN.")
    st.stop()
if not any(found.values()):
    st.error("None of your tables are on MotherDuck yet. Run your pipeline (GitHub Actions → "
             "Run workflow) and reload this page.")
    st.stop()

refreshed = last_refresh()
st.caption(f"Data refreshed {refreshed} by a daily pipeline." if refreshed else
           "Refresh time unknown: has your pipeline published yet?")

with st.sidebar:
    st.header("About this data")
    st.write("Answers come only from these tables:")
    for t, cols in found.items():
        st.write(f"- `{t}`" + ("" if cols else " (not on MotherDuck yet)"))
    st.write("Every answer shows the SQL and rows behind it, so you can check it.")
    if DICTIONARY:
        with st.expander("Data dictionary"):
            st.markdown(DICTIONARY)
    st.caption(f"AI model: {st.session_state.get('model_used', MODELS[0])}. Free tier: questions "
               "and table descriptions are sent to Google. Public data only.")

if "history" not in st.session_state:
    st.session_state.history = []

st.write("**Try one:**")
cols = st.columns(2)
clicked = None
for i, q in enumerate(settings.get("examples", [])[:6]):
    if cols[i % 2].button(q, key=f"example{i}"):
        clicked = q

question = st.chat_input("Ask a question about this data") or clicked
if question:
    with st.spinner("Writing SQL, running it, reading the rows…"):
        try:
            st.session_state.history.insert(0, answer(question))
        except AIError as e:
            st.session_state.history.insert(0, {"question": question, "status": "ai", "text": str(e)})

for item in st.session_state.history:
    st.divider()
    st.subheader(item["question"])
    if item["status"] == "ok":
        st.success(item["text"])
    elif item["status"] == "cannot":
        st.warning("This data can't answer that. " + item["text"])
    else:
        st.error(item["text"])
    if item.get("sql"):
        with st.expander("How this answer was made", expanded=item is st.session_state.history[0]):
            st.write("**1. The SQL the AI wrote**" + (" (it fixed its first try)" if item.get("fixed") else ""))
            st.code(item["sql"], language="sql")
            if "rows" in item:
                st.write(f"**2. The rows it returned** ({len(item['rows'])})")
                st.dataframe(item["rows"], hide_index=True)
