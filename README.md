# Data Infrastructure and Management in Context of AI

Columbia GSAPP · Fall 2026 · Tuesdays 5:30–7:30 PM

This repo is your workspace for the whole course. Each session adds one layer to it: by the end it holds a scheduled pipeline, a cloud database and a deployed AI app.

---

## First-time setup (about 10 minutes)

You need a GitHub account first. If you haven't already, also apply for the free [GitHub Student Developer Pack](https://education.github.com/pack) with your Columbia email. It raises your free Codespaces hours.

**1. Make your own copy of this repo**

- At the top of this page, click the green **Use this template** button → **Create a new repository**.
- **Owner:** your GitHub account. **Name:** something like `data-infra-project`.
- Choose **Public**. (Course data is public, and public repos get unlimited free GitHub Actions minutes, which you'll use in Session 4. Never put API keys or private data in it.)
- Click **Create repository**.

**2. Open it in a Codespace**

- In *your new repo* (not the course template), click the green **Code** button → **Codespaces** tab → **Create codespace on main**.
- A coding environment opens in your browser. The first launch takes 2–4 minutes while it installs the course libraries. Wait until the terminal at the bottom stops scrolling.

**3. Check that everything works**

In the terminal at the bottom of the screen, type:

```
python check_setup.py
```

You should see `Your workspace is ready.` If not, see *Troubleshooting* below.

**4. Start Lab 1**

Open `notebooks/lab1_first_query.ipynb` from the file list on the left and follow the instructions inside.

---

## What's in this repo

| Path | What it is |
|---|---|
| `notebooks/` | Lab notebooks, starting with `lab1_first_query.ipynb` |
| `labs/` | Written parts of each lab, such as the Lab 1 lifecycle map |
| `data/` | Sample datasets (see `data/README.md`) |
| `requirements.txt` | The Python libraries the course uses |
| `.devcontainer/` | Settings that tell Codespaces how to build your workspace. You don't need to edit this |
| `check_setup.py` | Confirms your workspace is ready |

---

## Saving your work

Changes in a Codespace are **not on GitHub until you commit and push.**

1. Click the **Source Control** icon in the left sidebar (it looks like a branch).
2. Type a short message, such as `Lab 1 done`.
3. Click **Commit**, then **Sync Changes**.

---

## Making your free hours last

A free account includes 120 core-hours a month (180 with the Student Pack). This workspace uses a 2-core machine, so that's **60 hours** of use (90 with the Pack). That's plenty for this course if you:

- **Stop your Codespace when you finish:** click **Codespaces** in the bottom-left corner → **Stop Current Codespace**. (It also stops on its own after 30 minutes idle.)
- **Reuse one Codespace.** Reopen it from [github.com/codespaces](https://github.com/codespaces) instead of creating a new one each time.
- **Delete old Codespaces** you no longer need at [github.com/codespaces](https://github.com/codespaces).

---

## Keeping secrets safe

Starting in Session 3 you'll use API keys (MotherDuck, Gemini). **Never paste a key into a notebook, a file you commit, or an AI tool.** We'll store them as Codespaces secrets, GitHub Actions secrets and Streamlit secrets. `.gitignore` already blocks `.env` and `.streamlit/secrets.toml` from being committed.

---

## Troubleshooting

| Problem | Fix |
|---|---|
| `check_setup.py` says a library is missing | Run `pip install --user -r requirements.txt` in the terminal, then try again |
| The notebook asks you to **Select Kernel** | Choose **Python Environments** → the Python 3.12 option |
| A cell shows `[*]` and never finishes | Click **Restart** at the top of the notebook, then run the cells again from the top |
| "You've used all your Codespaces hours" | Use [Google Colab](https://colab.research.google.com) as a backup and tell the instructor |
| Can't find your Codespace | It's listed at [github.com/codespaces](https://github.com/codespaces) |
