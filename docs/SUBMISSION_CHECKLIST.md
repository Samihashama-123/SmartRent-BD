# PUB CSE FEST 2026 — GitHub Submission Checklist

**Submission deadline: Wednesday, October 28, 2026, 8:00 AM (Bangladesh time).** The organizer requires the complete project source code, demonstration video and evaluation documents in an accessible GitHub repository, then the repo link and team details submitted using the provided Google Form.

## Before upload

- [ ] Student / Landlord / Admin logins tested using real freshly created sample accounts.
- [ ] C3 mandatory workflows reviewed against `REQUIREMENTS_MATRIX.md`.
- [ ] Both innovation pages (/compare, /living-cost) work in actual browser.
- [ ] English and Bengali pages checked on desktop and mobile.
- [ ] Map geocoding tested with Internet; Bogura searched as location and only existing approved listings appear as markers.
- [ ] HTTP status errors and blocked authorization actions display correctly.
- [ ] No fake ID/document ownership, payment processor or verified-tenant claim in presentation.
- [ ] Demo video recorded, exported, and plays with readable text.
- [ ] `README.md`, `docs/`, code and `requirements.txt` committed.
- [ ] **NO real names, phones, NIDs, auth tokens, passwords or `.env`** published.

## Create and push repository

Create an empty GitHub repository for your team, then run **inside the extracted `SmartRent_BD` folder** (Git Bash or VS Code terminal):

```bash
git init
git status
git add .gitignore README.md requirements.txt requirements-dev.txt \
  main.py app/ templates/ static/ tests/ docs/ run.bat run.sh setup_admin.py seed_data.py
# Carefully inspect what is about to be published:
git diff --cached --stat
git diff --cached --name-only
git commit -m "Complete SmartRent BD hackathon submission"
git branch -M main
# Replace USERNAME/REPO with your real team repository:
git remote add origin https://github.com/USERNAME/REPO.git
git push -u origin main
```

If the folder is ALREADY a Git repository, do not run a new `git init` or blindly add a remote. Run `git status`, `git remote -v`, `git add ...`, `git commit`, `git push` on the existing branch according to your team workflow. Do not force-push anyone else's work.

**Note:** `.gitignore` intentionally excludes `smartrent.db`, `smartrent_backup.db`, `.venv`, `.env`, cached files and local ZIP files. The code creates its own empty SQLite database on first run. The bundled ZIP can contain your original local DB for continuity, but the public repo must not expose it.

## Demo video in GitHub

- Prefer a small MP4 or an externally hosted viewable link clearly documented in the `README.md`.
- Ensure organizers can access the video without sign-in restrictions.
- Check GitHub file size restrictions; do not push huge videos into source history.
- Follow `docs/DEMO_VIDEO_SCRIPT.md` for a short, truthful flow.

## Verify submission

1. Visit your GitHub repository in an **incognito browser**; verify it is public or accessible to organizers.
2. Confirm `README.md` is rendered; `app/`, `templates/`, `static/`, `tests/` and `docs/` are visible.
3. Copy the exact repository URL.
4. Fill in the organizers' form with repository link and correct team details: **https://forms.gle/DTAJEg6b7tVSNRZw9**.
5. Submit before **October 28, 2026 at 8:00 AM**; preserve the submission confirmation.

### Feature freeze

After submission, **do not add/remove features or change original functionality**. Only fix existing bugs/technical issues and improve UI/UX, per organizer notice.
