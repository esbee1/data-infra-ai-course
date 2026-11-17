"""
pipeline.py · Labs 3 + 4
A scheduled data pipeline: EXTRACT -> LOAD -> VALIDATE -> TRANSFORM -> PUBLISH.

Run it by hand in your Codespace terminal:
    python pipeline.py
GitHub Actions runs the same file every day (see .github/workflows/pipeline.yml).

This is a second worked example: NYC 311 heat and hot water complaints.
Copy the four ### YOUR PROJECT ### blocks into your own pipeline.py as a model. To make it yours,
edit only the four blocks marked  ### YOUR PROJECT ###  below.
"""

import os
import sys
import time
from datetime import datetime, timezone

import duckdb
import pandas as pd
import requests


# =============================================================================
### YOUR PROJECT ### 1. Settings
# =============================================================================
PROJECT_TABLE = "heat_complaints"    # name of your final table on MotherDuck
MIN_ROWS = 100                       # fewer rows than this means something went wrong
DAYS_BACK = 14                       # take a fresh snapshot of the last two weeks each run

# NYC Open Data: 311 Service Requests from 2010 to Present
NYC_311_URL = "https://data.cityofnewyork.us/resource/erm2-nwe9.json"


# =============================================================================
# Helpers: logging, polite requests with retries, two common paging styles
# =============================================================================
def log(step, message):
    """Every line gets a time and a step name, so the run log tells a story."""
    now = datetime.now(timezone.utc).strftime("%H:%M:%S")
    print(f"{now}  [{step:<9}] {message}", flush=True)


def get_json(url, params=None, tries=5, pause=3):
    """GET a URL and return its JSON. Retries up to 5 times if the server is slow or busy."""
    for attempt in range(1, tries + 1):
        try:
            r = requests.get(url, params=params, timeout=(10, 90))   # 10s to connect, 90s to answer
            if r.status_code == 429 or r.status_code >= 500:   # busy or broken: worth retrying
                raise requests.HTTPError(f"status {r.status_code}")
            r.raise_for_status()                                # 4xx: our mistake, don't retry
            return r.json()
        except (requests.ConnectionError, requests.Timeout, requests.HTTPError) as e:
            if attempt == tries or (isinstance(e, requests.HTTPError) and "status" not in str(e)):
                raise
            log("extract", f"attempt {attempt} failed ({e}); retrying in {pause * attempt}s")
            time.sleep(pause * attempt)


def fetch_world_bank(url, params, per_page=250):        # smaller pages answer faster
    """World Bank style: [page info, records], with page=1, 2, 3..."""
    rows, page = [], 1
    while True:
        meta, records = get_json(url, {**params, "format": "json", "per_page": per_page, "page": page})
        rows.extend(records or [])
        log("extract", f"page {meta['page']} of {meta['pages']}: {len(records or [])} rows")
        if page >= meta["pages"]:
            return rows, int(meta["total"])
        page += 1
        time.sleep(0.5)                   # be polite between pages


def fetch_socrata(url, params=None, page_size=1000, max_pages=20):
    """NYC Open Data / Socrata style: a plain list, paged with $limit and $offset."""
    rows = []
    for i in range(max_pages):
        batch = get_json(url, {**(params or {}), "$limit": page_size, "$offset": i * page_size})
        rows.extend(batch)
        log("extract", f"page {i + 1}: {len(batch)} rows")
        if len(batch) < page_size:        # a short page means we've reached the end
            break
        time.sleep(0.5)
    return rows


# =============================================================================
### YOUR PROJECT ### 2. EXTRACT: fetch from the API and flatten into tables
# =============================================================================
def extract():
    since = (datetime.now(timezone.utc) - pd.Timedelta(days=DAYS_BACK)).strftime("%Y-%m-%dT00:00:00")
    rows = fetch_socrata(NYC_311_URL, {
        "$select": "unique_key, created_date, complaint_type, borough, incident_zip",
        "$where": f"complaint_type = 'HEAT/HOT WATER' AND created_date >= '{since}'",
        "$order": "unique_key",              # a stable order, so pages don't overlap
    })
    df = pd.json_normalize(rows)
    for col in ["unique_key", "created_date", "complaint_type", "borough", "incident_zip"]:
        if col not in df.columns:            # Socrata leaves out fields that are empty
            df[col] = None
    df = df[["unique_key", "created_date", "complaint_type", "borough", "incident_zip"]]
    df["created_date"] = pd.to_datetime(df["created_date"])
    df["incident_zip"] = df["incident_zip"].astype("string").str.zfill(5)   # keep leading zeros
    return {"heat_raw": df}


# =============================================================================
### YOUR PROJECT ### 3. VALIDATE: the checks that define "ready"
# =============================================================================
BOROUGHS = "('BRONX', 'BROOKLYN', 'MANHATTAN', 'QUEENS', 'STATEN ISLAND', 'UNSPECIFIED')"
CHECKS = [
    ("enough rows arrived",
     f"SELECT CASE WHEN count(*) >= {MIN_ROWS} THEN 0 ELSE 1 END FROM heat_raw"),
    ("unique_key present and unique",
     "SELECT count(*) - count(DISTINCT unique_key) + count(*) FILTER (WHERE unique_key IS NULL) FROM heat_raw"),
    ("borough is an allowed value",
     f"SELECT count(*) FROM heat_raw WHERE borough NOT IN {BOROUGHS}"),
    ("no dates in the future",
     "SELECT count(*) FROM heat_raw WHERE created_date > now()::TIMESTAMP + INTERVAL 1 DAY"),
    ("fresh: newest complaint is under 3 days old",
     "SELECT CASE WHEN max(created_date) >= now()::TIMESTAMP - INTERVAL 3 DAY THEN 0 ELSE 1 END FROM heat_raw"),
]


# =============================================================================
### YOUR PROJECT ### 4. TRANSFORM: build the tables your app will use
# =============================================================================
TRANSFORMS = [
    (PROJECT_TABLE, """
        SELECT unique_key, created_date, created_date::DATE AS created_day, borough, incident_zip
        FROM heat_raw
        WHERE borough <> 'UNSPECIFIED'          -- can't be placed on a map; dropped on purpose
    """),
    ("heat_by_borough_day", f"""
        SELECT borough, created_day, count(*) AS complaints
        FROM {PROJECT_TABLE}
        GROUP BY ALL
    """),
]


# =============================================================================
# The pipeline itself. You shouldn't need to change anything below this line.
# =============================================================================
class ValidationError(Exception):
    pass


def load(con, tables):
    for name, df in tables.items():
        con.register("incoming", df)
        con.sql(f"CREATE OR REPLACE TABLE {name} AS SELECT * FROM incoming")   # replace, never append
        con.unregister("incoming")
        log("load", f"{name}: {con.sql(f'SELECT count(*) FROM {name}').fetchone()[0]} rows")


def break_on_purpose(con, tables):
    """Only when BREAK_IT=true: empty the first raw table, to prove the checks stop the run."""
    name = next(iter(tables))
    con.sql(f"DELETE FROM {name}")
    log("load", f"BREAK_IT is on: emptied {name} on purpose")


def validate(con, tables):
    # One built-in check per raw table (an empty download should never be published),
    # then your checks.
    builtin = [(f"{t} is not empty", f"SELECT CASE WHEN count(*) > 0 THEN 0 ELSE 1 END FROM {t}")
               for t in tables]
    failures = []
    for name, sql in builtin + CHECKS:
        problems = con.sql(sql).fetchone()[0]
        status = "PASS" if problems == 0 else "FAIL"
        log("validate", f"{status}  {name}  ({problems} problem rows)")
        if problems:
            failures.append(name)
    if failures:
        raise ValidationError(f"{len(failures)} check(s) failed: {failures}")
    log("validate", "all checks passed")


def transform(con):
    for name, sql in TRANSFORMS:
        con.sql(f"CREATE OR REPLACE TABLE {name} AS {sql}")
        log("transform", f"{name}: {con.sql(f'SELECT count(*) FROM {name}').fetchone()[0]} rows")


def motherduck_token():
    # GitHub stores secret names in capitals; DuckDB looks for either spelling.
    token = os.environ.get("MOTHERDUCK_TOKEN") or os.environ.get("motherduck_token")
    if token:
        os.environ["motherduck_token"] = token
    return token


def publish(con):
    if not motherduck_token():
        if os.environ.get("GITHUB_ACTIONS"):
            raise RuntimeError("MOTHERDUCK_TOKEN secret is missing. Add it under "
                               "Settings -> Secrets and variables -> Actions.")
        log("publish", "no MotherDuck token found: skipping publish (local test only)")
        return
    md = duckdb.connect("md:")
    md.sql("CREATE DATABASE IF NOT EXISTS course")
    for name, _ in TRANSFORMS:
        md.register("to_share", con.sql(f"SELECT * FROM {name}").df())
        md.sql(f"CREATE OR REPLACE TABLE course.main.{name} AS SELECT * FROM to_share")
        md.unregister("to_share")
        n = md.sql(f"SELECT count(*) FROM course.main.{name}").fetchone()[0]
        log("publish", f"course.main.{name}: {n} rows on MotherDuck")
    md.sql(f"""CREATE OR REPLACE TABLE course.main.pipeline_runs AS
               SELECT '{PROJECT_TABLE}' AS project_table, now() AS last_success""")
    md.close()


def main():
    started = time.time()
    log("start", f"pipeline for '{PROJECT_TABLE}'")
    con = duckdb.connect()            # a fresh in-memory database every run
    try:
        tables = extract()
        load(con, tables)
        if os.environ.get("BREAK_IT", "").lower() == "true":
            break_on_purpose(con, tables)
        validate(con, tables)
        transform(con)
        publish(con)
    except ValidationError as e:
        log("STOPPED", f"{e}. Nothing was published; yesterday's tables are untouched.")
        sys.exit(1)                   # a non-zero exit turns the GitHub Actions run red
    except Exception as e:
        log("STOPPED", f"{type(e).__name__}: {e}")
        sys.exit(1)
    log("done", f"success in {time.time() - started:.0f}s")


if __name__ == "__main__":
    main()
