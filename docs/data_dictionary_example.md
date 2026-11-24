# Data dictionary · EXAMPLE (NYC 311 heat complaints, class demo)

<!-- A filled-in version of data_dictionary.md. Example values are illustrative. -->

## Part 1 · About the project

**Project:** Heat and hot water complaints made to NYC 311 in the last 7 days, by borough and ZIP code.

**Source:** NYC Open Data, 311 Service Requests (dataset erm2-nwe9), https://data.cityofnewyork.us/resource/erm2-nwe9.json

**Refreshed:** Daily at about 6 AM New York time by GitHub Actions. Each run replaces every table with the last 7 days of complaints, so older days drop off.

**Removed on purpose:** Complaints with borough "UNSPECIFIED", because they can't be placed in a borough. Only complaint type "HEAT/HOT WATER" is kept.

---

## Part 2 · The tables

### Table 1: `course.main.heat_complaints`

**What it is:** The clean table

**One row is:** one complaint

**Built from:** raw

| Column | Type | What it means | Units or allowed values | Example |
|---|---|---|---|---|
| unique_key | text | The city's ID for the complaint | unique; never repeated | 63012345 |
| created_date | timestamp | When the complaint was made | New York time | 2026-11-15 21:42:00 |
| created_day | date | The day the complaint was made | date only | 2026-11-15 |
| borough | text | Borough of the building | BRONX, BROOKLYN, MANHATTAN, QUEENS, STATEN ISLAND | BRONX |
| incident_zip | text | ZIP code of the building | 5 digits; can be empty | 10467 |

### Table 2: `course.main.heat_by_borough_day`

**What it is:** A trend

**One row is:** one borough on one day

**Built from:** heat_complaints

| Column | Type | What it means | Units or allowed values | Example |
|---|---|---|---|---|
| borough | text | Borough | the five boroughs | BROOKLYN |
| created_day | date | Day | last 7 days | 2026-11-15 |
| complaints | integer | Heat complaints in that borough that day | count | 412 |

### Table 3: `course.main.heat_borough_summary`

**What it is:** Key metrics

**One row is:** one borough, over the last 7 days

**Built from:** heat_complaints

| Column | Type | What it means | Units or allowed values | Example |
|---|---|---|---|---|
| borough | text | Borough | the five boroughs | BRONX |
| total_complaints | integer | All heat complaints in the 7 days | count | 3,420 |
| avg_per_day | number | Average complaints per day | count per day, 1 decimal | 488.6 |
| pct_of_city | number | This borough's share of all complaints in the city | percent, 0–100; the five add to 100 | 31.4 |
| zip_codes_affected | integer | ZIP codes with at least one complaint | count | 25 |

### Table 4: `course.main.heat_top_zips`

**What it is:** A ranking

**One row is:** one ZIP code (top 20 only)

**Built from:** heat_complaints

| Column | Type | What it means | Units or allowed values | Example |
|---|---|---|---|---|
| incident_zip | text | ZIP code | 5 digits | 10467 |
| borough | text | Borough the ZIP is in | the five boroughs | BRONX |
| complaints | integer | Heat complaints in that ZIP in the 7 days | count | 298 |

---

## Part 3 · What this data can't tell you

1. Only the last 7 days. It can't show last winter or compare years.
2. A complaint is a call, not a confirmed problem. Several tenants in one building can complain about the same outage.
3. Counts aren't adjusted for population or number of buildings, so bigger boroughs will naturally have more.

## Part 4 · Example questions it can answer

1. Which borough had the most heat complaints this week? (heat_borough_summary)
2. What share of complaints came from the Bronx? (heat_borough_summary)
3. Which five ZIP codes were hardest hit? (heat_top_zips)
4. Were complaints rising or falling over the week in Brooklyn? (heat_by_borough_day)
