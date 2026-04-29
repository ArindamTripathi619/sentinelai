# 🤝 Contributing to SentinelAI

This guide explains the Git workflow for the team. Read this before touching any code.

---

## Step 1 — Fork & Clone

1. Go to the main repo on GitHub
2. Click **Fork** → creates a copy under your GitHub account
3. Clone your fork:
   ```bash
   git clone https://github.com/YOUR_USERNAME/sentinelai.git
   cd sentinelai
   ```
4. Add the main repo as upstream (so you can pull updates):
   ```bash
   git remote add upstream https://github.com/ARINDAM_USERNAME/sentinelai.git
   ```

---

## Step 2 — Create Your Branch

Each person works on exactly one branch. Do not touch other branches.

```bash
# Create and switch to your assigned branch
git checkout -b feature/YOUR-ASSIGNED-BRANCH

# Atul:      feature/backend-core
# Akash:     feature/security-engine
# Debarshi:  feature/admin-dashboard
# Parthiv:   feature/scripts-and-docs
```

---

## Step 3 — Do Your Work

- Make changes only in the files assigned to you (see README for assignments)
- Commit frequently with clear messages:

```bash
git add .
git commit -m "feat: implement velocity rule in rules.py"
git commit -m "fix: handle null user agent in duplicate device check"
git commit -m "chore: add docstrings to scorer functions"
```

**Commit message format:** `type: short description`
- `feat:` — new feature
- `fix:` — bug fix
- `chore:` — cleanup, docs, formatting
- `test:` — adding tests

---

## Step 4 — Stay Updated

Before opening a PR, pull the latest changes from main:

```bash
git fetch upstream
git rebase upstream/main
# Resolve any conflicts, then:
git push origin feature/YOUR-ASSIGNED-BRANCH --force-with-lease
```

---

## Step 5 — Open a Pull Request

1. Push your branch: `git push origin feature/YOUR-ASSIGNED-BRANCH`
2. Go to the main repo on GitHub
3. Click **"Compare & pull request"**
4. Fill in the PR description:
   - What did you build?
   - How can Arindam test it?
   - Any blockers or things you skipped?
5. Assign **Arindam** as reviewer
6. Submit the PR and ping Arindam in the group chat

---

## Step 6 — Wait for Review

Arindam will review within 30 minutes during the hackathon. He may:
- **Approve and merge** → your work is in `main` ✅
- **Request changes** → fix the noted issues and push again
- **Comment** → answer questions in the PR thread

---

## Rules

- **Never push directly to `main`** — it's protected
- **Only edit files in your assigned area** — coordinate in chat if you need to touch shared files
- **Keep PRs focused** — one feature per PR, don't bundle unrelated changes
- **If you're blocked**, message the team immediately — don't sit stuck for more than 20 minutes
- **If you finish early**, help with testing or documentation

---

## Who Owns What

| File/Folder | Owner |
|---|---|
| `backend/main.py`, `auth.py`, `models.py`, `database.py` | Atul |
| `backend/rules.py`, `scorer.py`, `ml_model.py` | Akash |
| `frontend/src/` (all), `frontend/src/sdk/behavioral.js` | Debarshi |
| `scripts/`, `backend/geo.py`, `docs/`, `README.md` | Parthiv |
| `API.md`, `.env.example`, `requirements.txt`, repo structure | Arindam |

If you need to edit a file outside your area, ask the owner first.

---

## Getting Help

1. Check `API.md` for the endpoint contract
2. Check `docs/architecture.md` for how components connect
3. Ask in the group chat
4. Ask Arindam
