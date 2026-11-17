"""
pipeline.py · Labs 3 + 4
A scheduled data pipeline: EXTRACT -> LOAD -> VALIDATE -> TRANSFORM -> PUBLISH.

Run it by hand in your Codespace terminal:
    python pipeline.py
GitHub Actions runs the same file every day (see .github/workflows/pipeline.yml).

This is a second worked example: World Bank urban population (a page-numbered API).
Copy the four ### YOUR PROJECT ### blocks into your own pipeline.py as a model.
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
PROJECT_TABLE = "urban_population"   # name of your final table on MotherDuck
MIN_ROWS = 500                       # fewer rows than this means something went wrong

# World Bank example
WB_BASE = "https://api.worldbank.org/v2"
WB_INDICATOR = "SP.URB.TOTL.IN.ZS"   # urban population, % of total
WB_YEARS = "2015:2023"


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
            r = requests.get(url, params=params, timeout=(10, 120))  # 10s to connect, 120s to answer
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
# Return a dict of {table_name: DataFrame}. These become your raw tables.
# =============================================================================
def extract():
    # The indicator endpoint is slow per request, so ask for fewer, bigger pages
    rows, expected = fetch_world_bank(f"{WB_BASE}/country/all/indicator/{WB_INDICATOR}",
                                      {"date": WB_YEARS}, per_page=1000)
    if len(rows) != expected:
        log("extract", f"WARNING: got {len(rows)} rows, API says {expected}")

    urban = pd.json_normalize(rows).rename(columns={
        "countryiso3code": "country_code", "country.value": "country",
        "date": "year", "value": "urban_pct",
    })[["country_code", "country", "year", "urban_pct"]]
    urban["year"] = urban["year"].astype(int)
    # Decision: a few World Bank rows have no 3-letter country code (they are groupings,
    # not countries). Our key is country_code + year, so rows without a code can't be used.
    no_code = (urban["country_code"].isna()) | (urban["country_code"].str.strip() == "")
    if no_code.any():
        names = sorted(urban.loc[no_code, "country"].unique())
        log("extract", f"dropping {no_code.sum()} rows with no country code: {names}")
    urban = urban[~no_code]

    country_rows, _ = fetch_world_bank(f"{WB_BASE}/country", {})
    countries = pd.json_normalize(country_rows).rename(columns={
        "id": "country_code", "region.value": "region", "incomeLevel.value": "income_level",
    })[["country_code", "region", "income_level"]]
    countries["region"] = countries["region"].str.strip()

    return {"urban_raw": urban, "countries": countries}

    # --- Socrata (NYC Open Data) version: replace everything above with something like ---
    # rows = fetch_socrata("https://data.cityofnewyork.us/resource/xxxx-xxxx.json",
    #                      {"$where": "created_date >= '2026-01-01'"})
    # df = pd.json_normalize(rows)
    # df = df.rename(columns={...})[[...]]          # keep and rename what you need
    # df["created_date"] = pd.to_datetime(df["created_date"])
    # return {"my_raw": df}


# =============================================================================
### YOUR PROJECT ### 3. VALIDATE: the checks that define "ready"
# Each check is (name, SQL that returns the number of PROBLEM rows). 0 = pass.
# They run against the raw tables, before anything is published.
# =============================================================================
CHECKS = [
    ("enough rows arrived",
     f"SELECT CASE WHEN count(*) >= {MIN_ROWS} THEN 0 ELSE 1 END FROM urban_raw"),
    ("keys present and unique (country_code, year)",
     """SELECT count(*) FROM (
            SELECT country_code, year FROM urban_raw
            GROUP BY ALL HAVING count(*) > 1 OR country_code IS NULL OR country_code = ''
        )"""),
    ("urban_pct between 0 and 100",
     "SELECT count(*) FROM urban_raw WHERE urban_pct NOT BETWEEN 0 AND 100"),
    ("under 25% of values missing",
     "SELECT CASE WHEN avg((urban_pct IS NULL)::INT) < 0.25 THEN 0 ELSE 1 END FROM urban_raw"),
    ("has data from 2022 or later",
     "SELECT CASE WHEN max(year) FILTER (WHERE urban_pct IS NOT NULL) >= 2022 THEN 0 ELSE 1 END FROM urban_raw"),
]


# =============================================================================
### YOUR PROJECT ### 4. TRANSFORM: build the tables your app will use
# A list of (table_name, SQL). Each becomes a table that gets published.
# =============================================================================
TRANSFORMS = [
    # Countries only: regions like "World" and "High income" are removed on purpose
    (PROJECT_TABLE, """
        SELECT u.country_code, u.country, c.region, c.income_level, u.year, u.urban_pct
        FROM urban_raw u
        JOIN countries c USING (country_code)
        WHERE c.region <> 'Aggregates'
    """),
    # A summary table: change in urban share, first year to latest year
    ("urban_change", f"""
        SELECT country, region,
               arg_min(urban_pct, year) AS pct_first,
               arg_max(urban_pct, year) AS pct_latest,
               round(pct_latest - pct_first, 1) AS change
        FROM {PROJECT_TABLE}
        WHERE urban_pct IS NOT NULL
        GROUP BY country, region
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
