# SmartRent BD — Role navigation, admin access and password recovery (v6)

## Admin setup and sign-in

From a VS Code terminal inside the project with the virtual environment active:

```bash
python setup_admin.py
```

Enter **your own admin email and a unique password** (12 characters or more).
The password input is hidden. The script creates only an admin account or updates an existing admin account with the same email. It will refuse to promote an existing student/landlord account. Credentials stay in the local SQLite database; NEVER commit this database to a public repository.

Admin sign-in: `http://127.0.0.1:8000/admin/login`, or the same `/login` page used by every role. After signing in without a protected `next` URL: student → `/profile`, landlord → `/landlord`, admin → `/admin`. A protected-page link takes priority over the default dashboard. Login cannot elevate role; the server checks role on protected pages.

## Role navigation

- Student: Home, Housing, Roommates, My Bookings, Mess Manager, Maintenance, Fair Rent, Compare, Living Cost, Rental Draft, Profile.
- Landlord: Home, Housing (public), My Properties/Visits/Bookings (in the dashboard), Maintenance, Rental Draft, Profile. Student-only financial comparison, roommate and mess links are hidden and their routes return **403** when visited as a landlord.
- Admin: Home, Housing (public), Admin Dashboard (verification and reports), Profile. Role-specific tools are not shown; server permission still applies.
- Guest: Home, Housing, Sign In, Create Account. Private actions redirect to sign-in.

## Forgot password: making real email arrive

1. Install dependencies from `requirements.txt` (includes `python-dotenv`).
2. Make a private `.env` file in the project root by copying `.env.example`.
3. Fill `SMARTRENT_SMTP_HOST`, `SMARTRENT_SMTP_PORT`, `SMARTRENT_SMTP_FROM`, `SMARTRENT_SMTP_USER` and `SMARTRENT_SMTP_PASSWORD` using your chosen **verified email provider's SMTP settings**. Often an app-specific email credential is required; an ordinary account password may not work.
4. Keep `SMARTRENT_PUBLIC_URL=http://127.0.0.1:8000` for testing reset links **on the same laptop**. For a deployed system use the actual HTTPS site URL.
5. Restart the server completely and request password reset for an email registered in the SmartRent user table. Check Inbox and Spam.
6. If SMTP is missing or connection/authentication fails, the UI reports that **no email was sent**, rather than pretending to succeed. Successful requests intentionally show the same generic response for registered/unregistered email addresses.

### Security

- `.env` / SQLite `.db` / credentials must not be pushed to GitHub. Check `git status` before committing.
- Reset tokens expire after 30 minutes; only SHA256 token hashes are stored. Reuse fails and old sessions are invalidated.
- Do not add a "show reset link in browser" feature; it compromises accounts.
- Password reset email **cannot work until an outgoing email service is configured**. This release includes the working SMTP integration and private configuration loading; no email account or SMTP login was provided, so live inbox delivery has not been verified.

## Replacing source safely

Stop the server, back up the whole current project, and extract **source-only** files into your existing project. Preserve `smartrent.db`, `.venv`, and your private `.env`. Install updated requirements and restart:

```bash
source .venv/Scripts/activate
python -m pip install -r requirements.txt
python -m uvicorn main:app --reload --port 8000
```

Check role-specific navigation after a logout/login, then the safety notice on `/listings/<id>`.
