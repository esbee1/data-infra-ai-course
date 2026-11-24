# Lab 5 · An AI app for your data

**Due Sunday, November 29, 11:59 PM.** Submit on CourseWorks: your **app URL** and your **repo link**.

Tonight you put a plain-English interface on the tables your pipeline publishes every morning. Anyone with the link can ask a question; the app writes SQL, runs it on MotherDuck, and shows the answer **with the SQL and rows behind it**.

```
question ──► Gemini writes SQL ──► guardrails check it ──► MotherDuck runs it
             (reads your data dictionary)                       │
answer ◄── Gemini explains the rows ◄───────────────────────────┘
```

You don't write Python. Like last week, there's an engine and a form:

| File | What it is | Do you edit it? |
|---|---|---|
| `app.py` | The app engine | No |
| `app.toml` | The app's form: title, example questions, AI model | **Yes** |
| `docs/data_dictionary.md` | What every table and column means. **The AI reads this** | **Yes** |
| `project.toml` | Your pipeline. The app reads its table list | Only to improve answers |
| `docs/app_evaluation.md` | Your five-question evaluation | **Yes** |

---

## In class

### 0. Get the files

In your Codespace terminal:

```
curl -fsSL https://raw.githubusercontent.com/esbee1/data-infra-ai-course/main/get_lab.sh | bash -s 5
```

### 1. Get a Gemini API key

1. Go to **aistudio.google.com** and sign in with a **personal** Google account (Columbia accounts may be blocked).
2. Click **Get API key** → **Create API key**. Copy it somewhere safe for the next 10 minutes.

This key is a password, like your MotherDuck token. It never goes in a file, a commit or a chat.

### 2. Fill in the form

- **`app.toml`**: change the title, the description, and the `examples` to three or four questions about *your* data. Start with your findings.
- **`docs/data_dictionary.md`**: make sure it describes every table in your `project.toml`. If it's still the empty template, fill in at least the columns of your summary table now.

Then **commit and sync** (Source Control → message `Lab 5 app` → Commit → Sync Changes). Streamlit reads your app from GitHub, not from your Codespace.

### 3. Deploy

1. Go to **share.streamlit.io** and sign in with GitHub.
2. Click **Create app** (top right) → **Yup, I have an app**.
3. **Repository:** your course repo. **Branch:** `main`. **Main file path:** `app.py`.
4. **App URL:** pick a short name, e.g. `heat-complaints-yourname`.
5. Click **Advanced settings**. Python version: **3.12**. In **Secrets**, paste these two lines with your real values, keeping the quotes:

   ```
   MOTHERDUCK_TOKEN = "eyJ...your token..."
   GEMINI_API_KEY = "...your Gemini key..."
   ```

6. **Save**, then **Deploy**. The first build takes 2–5 minutes.

### 4. Ask it something

Click an example question. Then open **How this answer was made**: the SQL the AI wrote and the rows it returned. That's how you check an answer instead of trusting it.

### 5. Start your evaluation

Open `docs/app_evaluation.md` and start on the five questions.

### If something goes wrong

| You see | Fix |
|---|---|
| *Missing secret* | share.streamlit.io → your app's **⋮** → **Settings** → **Secrets**. Check both names and the quotes |
| *None of your tables are on MotherDuck yet* | Run your pipeline: repo → **Actions** → **Run workflow**. Then reload the app |
| *The free AI tier is busy* | You've asked too many questions this minute. Wait a minute |
| *Gemini didn't accept the key* | Recopy the key from AI Studio into Secrets |
| *No AI model answered* | Google renamed a model. In `app.toml`, put the model name AI Studio shows first in `models` |
| *There's a typo in app.toml* | Check quotes and commas on the line it names |
| The app shows old settings | You haven't pushed. Commit and Sync, wait a minute, reload |
| Build fails | **Manage app** (bottom right) shows the log. Read the last red lines |

**Optional: run it in your Codespace.** Add `GEMINI_API_KEY` as a Codespaces secret (same place as `MOTHERDUCK_TOKEN`), restart the Codespace, then run `streamlit run app.py`.

---

## At home

1. **Five questions.** Fill in `docs/app_evaluation.md`: three from your findings (you know the right answers), one harder question, and one your data *can't* answer. Judge each: good, weak or wrong, and why.
2. **One improvement.** Fix your weakest answer by changing one thing: the data dictionary, `extra_instructions` in `app.toml`, or a table in `project.toml`. Push, ask again, and record before and after.
3. **What leaves your control.** Answer the short question at the end of the evaluation.
4. **Commit and sync.** Check that your app still works at its URL.

## Checklist

- [ ] App live at a public `.streamlit.app` URL
- [ ] `app.toml` has your title, description and 3–5 example questions
- [ ] Data dictionary covers every table in `project.toml`
- [ ] `docs/app_evaluation.md`: five questions judged, one improvement with before and after, the governance answer
- [ ] App URL and repo link submitted on CourseWorks

The project proposal is a separate assignment, also due November 29.
