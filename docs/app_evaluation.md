# App evaluation

<!--
Lab 5. Ask your app five questions and judge each answer like an editor would.
Use your findings (docs/findings.md) for the first three: you already know the right answer,
so you can tell whether the app got it right.
Open "How this answer was made" every time: read the SQL and the rows, not just the sentence.
-->

**App URL:** https://____________.streamlit.app

**Tables the app uses:** (from project.toml)

## The five questions

| # | Kind | Question you asked | What the app said | SQL right? (yes / partly / no) | Verdict (good / weak / wrong) | Why |
|---|---|---|---|---|---|---|
| 1 | From finding 1 | | | | | |
| 2 | From finding 2 | | | | | |
| 3 | From finding 3 | | | | | |
| 4 | A harder one: needs two tables, a date range, or a comparison | | | | | |
| 5 | One your data CAN'T answer: it should say so, not guess | | | | | |

**Verdict guide**

- **Good:** right number, right table, the sentence matches the rows.
- **Weak:** roughly right, but it used the wrong table, missed a filter, or the sentence overstates what the rows show.
- **Wrong:** wrong number, an error, or it made up an answer to a question the data can't answer.

## One improvement, tested

Pick your weakest answer. Change ONE thing, push, wait for the app to update (about a minute), and ask the same question again.

**Question:**

**What was wrong:**

**What I changed** (tick one and describe it):

- [ ] the data dictionary (`docs/data_dictionary.md`): a clearer meaning, units or allowed values
- [ ] `extra_instructions` in `app.toml`
- [ ] a new or changed table in `project.toml`

**Before:** (what it said)

**After:** (what it says now)

## What leaves your control

Every question sends your question, your table descriptions and some result rows to Google's free Gemini tier. In 2–3 sentences: is that acceptable for your data? What would you change before using this app with non-public data?

