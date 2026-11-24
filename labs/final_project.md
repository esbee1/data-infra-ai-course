# Final project · A system-ready data product

**Deliverable due Sunday, December 6, 11:59 PM** (40% of your grade).
**Presentations Tuesday, December 8** (20%).

Your final project is the system you've been building since October, finished and explained:

```
open data API ──► GitHub Actions, daily ──► MotherDuck ──► Streamlit app ◄──► Gemini
                  (pipeline + checks)       (your tables)   (anyone asks in plain English)
```

You have almost all of it already. The last two weeks are about making it **good**: reliable, well described, honest about its limits, and usable by someone who isn't you.

## What to submit on CourseWorks

1. **Repo URL** (public)
2. **App URL** (`.streamlit.app`)
3. **Architecture note**: `docs/architecture.md` in your repo, one page

Get the architecture note template in your Codespace terminal:

```
curl -fsSL https://raw.githubusercontent.com/esbee1/data-infra-ai-course/main/get_lab.sh | bash -s final
```

## What we grade (40%)

| Part | Weight | What "done well" looks like | Where we look |
|---|---|---|---|
| **Pipeline runs on schedule and fails loudly** | 12% | Runs daily on GitHub Actions; the most recent scheduled runs are green; a deliberately failed run shows it stops and publishes nothing | Actions tab, `project.toml` |
| **Validation reflects a clear definition of "ready"** | 8% | At least five checks, each with a `why`; they cover at least three quality dimensions (completeness, accuracy, consistency, freshness); thresholds you can defend | `project.toml` |
| **AI layer: documented, guarded, traceable** | 10% | Data dictionary describes every published table (grain, meaning, units, what was removed); guardrails on; answers show SQL and rows; your evaluation shows at least one improvement you tested | `docs/data_dictionary.md`, `app.toml`, `docs/app_evaluation.md` |
| **Usable by a non-technical person, at a public URL** | 5% | Clear title and description; 3–5 example questions that work; plain language; it answers or honestly declines | Your app |
| **Architecture note** | 5% | One page: the system, three real decisions with tradeoffs, known limits, what leaves your control | `docs/architecture.md` |

## The presentation (20%, December 8)

**4 minutes, then 2 minutes of questions asked live through your app.** Order is shared on December 1.

A structure that works:

| Time | Part | What to show |
|---|---|---|
| 0:30 | **The question** | Who needs this, and what they want to know |
| 1:30 | **Live demo** | Ask two questions. Open "How this answer was made" for one |
| 0:45 | **How it works** | Your system diagram, one pass from source to answer |
| 0:45 | **Decisions** | Your three decisions and their tradeoffs |
| 0:30 | **Limits** | One thing it handles well; one thing it can't do |

Graded on: functionality (it works, live), design integrity (the parts fit together), quality of architecture (decisions you can defend), and clarity (a non-technical listener could follow).

**Before you present:** open your app the morning of December 8 to wake it, and check your latest Actions run is green.

## Timeline

| Date | What |
|---|---|
| Nov 29 | Lab 5 + project proposal due |
| **Dec 1** | Workshop + peer review. Come with your app live. A classmate tests it; you get written feedback |
| Dec 1–6 | Push at least one improvement from your feedback. Write the architecture note |
| **Dec 6** | Deliverable due, 11:59 PM |
| Dec 7 | Rehearse once, out loud, with a timer |
| **Dec 8** | Present. Wake your app first |

**After December 6**, only fix things that break; the version we grade is the one in your repo at the deadline.

## Final checklist

- [ ] Pipeline: daily schedule on; the latest runs are green
- [ ] At least five checks in `project.toml`, each with a `why`
- [ ] Data dictionary covers every table in `project.toml`
- [ ] `app.toml`: title, description and 3–5 example questions written for a non-technical reader
- [ ] App works at its public URL; every answer shows its SQL and rows
- [ ] `docs/app_evaluation.md` complete, including a tested improvement
- [ ] At least one improvement pushed after peer review
- [ ] `docs/architecture.md`: one page, three decisions, limits, what leaves your control, AI use
- [ ] Repo URL, app URL and note submitted on CourseWorks
- [ ] No keys or tokens anywhere in your repo
