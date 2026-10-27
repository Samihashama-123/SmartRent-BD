# SmartRent BD v5 — Guest, Role Navigation & Password Recovery

## Guest browsing

- `/`, `/listings`, and `/listings/<id>` are visible without an account.
- Visitors cannot request visits, send booking requests, access private profiles, report a property, compare homes as a member, or submit reviews without signing in.
- Guest navigation displays Home, Find Housing, Sign in and Create account.
- Login pages offer **Browse homes without signing in**.

## Role-aware navigation

- Student: Find Housing, Roommate Matching, My Visits & Bookings, Mess Manager, Maintenance, Fair Rent, Comparison, Living Cost, Agreement and Profile.
- Landlord: Find Housing, My Properties, Maintenance, Fair Rent, Comparison, Living Cost, Agreement and Profile. **No Roommates or Mess Manager links.**
- Admin: Find Housing, Admin Dashboard and Profile. Student/landlord-only pages are forbidden by the server, not merely hidden in the header.
- Restricted pages respond with HTTP 403 and a dedicated bilingual explanation if a logged-in user manually visits a forbidden URL.
- Public pages can still showcase features as marketing, but services require the matching account role.

## Password reset: genuine email delivery, not pretend success

A **Forgot Password?** link is added under the login password field. Reset flow:

1. Request reset by email, protected by existing CSRF cookie.
2. If SMTP is configured, the server creates a **random, single-use token**, saves only its SHA-256 hash and emails a link with a **30-minute expiry**.
3. The reset form validates the token and updates the salted PBKDF2 password hash; all old login sessions and reset tokens for the user are revoked.
4. Nonexistent account emails get a generic response. The server throttles repeated requests to the same account for two minutes.
5. **If SMTP is not configured, the interface explicitly says email delivery is unavailable.** No fake success and no insecure in-browser reset code.

### Configuration for locally hosted SMTP (optional)

Set these **environment variables privately before starting the server**:

- `SMARTRENT_SMTP_HOST` — SMTP host
- `SMARTRENT_SMTP_PORT` — `587` with STARTTLS (default) or `465` with TLS
- `SMARTRENT_SMTP_FROM` — verified sender address
- `SMARTRENT_SMTP_USER` — SMTP username (if required)
- `SMARTRENT_SMTP_PASSWORD` — SMTP password or provider-issued app credential
- `SMARTRENT_PUBLIC_URL` — the externally accessible base URL of the deployed site (e.g. `https://housing.example.org`)

For a local-only demo, you can try SMTP delivery to a mailbox on the same computer, but `http://127.0.0.1:8000` reset links only work on the local machine hosting the project.

**Windows PowerShell** (example host and sender, not real credentials):

```powershell
$env:SMARTRENT_SMTP_HOST = 'smtp.example.org'
$env:SMARTRENT_SMTP_PORT = '587'
$env:SMARTRENT_SMTP_FROM = 'noreply@example.org'
$env:SMARTRENT_SMTP_USER = 'smtp-login'
$env:SMARTRENT_SMTP_PASSWORD = 'configured-privately'
$env:SMARTRENT_PUBLIC_URL = 'http://127.0.0.1:8000'
python -m uvicorn main:app --reload --port 8000
```

These values apply only to that PowerShell session. **Never commit real passwords or a populated `.env` to GitHub.** No `.env` auto-loader is required by the app; environment variables must be exported into the server's own process.

## Data preservation

The **source-only update** does not contain `smartrent.db`; apply it to your existing project to preserve new users and bookings. Always stop the server and back up the project first. The new password token table is created using `CREATE TABLE IF NOT EXISTS` at startup.

## Checks

Run `python -m pytest -q` after installing development test requirements. Server/route and template tests cover guest access, role-aware navigation, password reset and existing booking workflows. Live real SMTP delivery and cross-device UI clicks require manual testing.
