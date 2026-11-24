# Architecture note

<!--
Final project. Keep this to ONE page: about 400–500 words plus the diagram.
Write it for a smart reader who has never seen your project, like a planner in a city agency.
Fill in every ____ and replace the (notes in brackets).
-->

**Project:** ____________

**App:** https://____________.streamlit.app   **Repo:** https://github.com/____/____

**Who it's for and what it answers:** (one sentence, e.g. "Tenant organizers who want to know which ZIP codes had the most heat complaints this week.")

## The system

```
[ Source: ________________ API ]
        │  pulled daily at __:__ by GitHub Actions (pipeline.py + project.toml)
        ▼
[ Checks: __ rules ]──── any fail ──► run stops, red X, nothing published
        │  all pass
        ▼
[ MotherDuck: __ tables ]  (clean table: ________; analysis: ________, ________)
        │
        ▼
[ Streamlit app ]◄────► [ Gemini (________) writes SQL from docs/data_dictionary.md ]
        │
        ▼
[ Someone asks: "______________________________?" ]
```

## Three decisions and their tradeoffs

Pick three decisions you actually made. Good places to look: how much data to pull and how often; what "ready" means (a check and its threshold); which analysis tables to build; how you described a tricky column; what you send to the AI.

| Decision | What I chose | What I didn't choose | The tradeoff: what I gained, what I gave up |
|---|---|---|---|
| 1 | | | |
| 2 | | | |
| 3 | | | |

## What it handles well, and what it can't do

**Handles well:** (one thing, with an example question it answers reliably)

**Known limits:** (2–3 honest limits: dates not covered, questions it gets wrong, places or groups missing from the data, how fresh it really is)

1.
2.

## What leaves my control

(2–3 sentences: what is sent to Gemini with each question, whether that's acceptable for this data, and what you'd change before using non-public data.)

## AI use

(Per the syllabus: if you used an AI tool substantially for this project, say how. Transparency is not penalized.)
