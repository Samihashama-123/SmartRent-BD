# SmartRent BD
### Student Housing & Roommate Matching Platform · PUB CSE FEST 2026

SmartRent BD is a **working, locally hosted full-stack web application** that connects university students looking for accommodation with landlords, helps students compare housing and roommates, and provides a structured set of tenant/landlord workflows. The app uses real SQLite persistence and session-based authentication. It does **not** process real payments.

**Stack:** Python 3.11+, FastAPI, Jinja2, SQLite, HTML/CSS/JavaScript, Leaflet/OpenStreetMap. Requires an internet connection for externally hosted map tiles, geocoding, icon fonts, and some image assets.

**v6 navigation & login update (Oct 27, 2026):** Admin login: `/admin/login` → dashboard `/admin`. Students and landlords open their own dashboards after login. Landlords no longer see student-only Living Cost, Comparison, Fair Rent or Mess features in their menus, and cannot access these URLs directly. The bilingual property Safety Notice has a repaired icon layout. SMTP email requires private `.env` settings; see `docs/FINAL_LOGIN_NAV_EMAIL_v6.md`.

## 1. Quick start (Windows / VS Code)

1. Extract the ZIP into a new folder. Open the inner `SmartRent_BD` folder in VS Code.
2. Double-click **`run.bat`**, or run it from a VS Code Terminal. It creates a local `.venv`, installs requirements, and starts the server.
3. Visit **http://127.0.0.1:8000/**. Browse public homes before deciding to sign in or register.
4. **New student or landlord:** choose **Create account** to register. To create an administrator account, use the separate local-only setup command below.
5. Stop the server with `Ctrl+C` in its terminal.

### Alternative (macOS/Linux)

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m uvicorn main:app --reload --port 8000
```

### Set up administrator account

From the project root, after installing dependencies:

```bash
python setup_admin.py
```

Follow the terminal prompts to create an admin account or set a password for an existing admin email. This changes the local SQLite database only. **Never publish admin passwords**. Some pre-existing sample accounts in the bundled database may not have passwords; create new student/landlord accounts instead of relying on them.

Read **[`docs/FINAL_LOGIN_NAV_EMAIL_v6.md`](docs/FINAL_LOGIN_NAV_EMAIL_v6.md)** for role-based navigation, guest browsing, and optional SMTP password recovery. Forgot Password uses real SMTP, configured privately through a local `.env` file. No email is sent before you configure SMTP and verify your sender.

## 2. Accounts and real workflows

| Role | What the user can do |
|---|---|
| **Student / Tenant** | Create a profile; filter approved properties; open maps; save searches and receive in-app matches on newly approved properties; request a viewing; request a booking after a landlord-scheduled visit; review only after landlord booking confirmation; report suspected scams; compare homes; estimate total living cost; use private roommate and mess workflows. |
| **Owner / Landlord** | Create and edit housing listings with photos, details, and bilingual optional text; respond to visit requests, schedule visits and approve/decline booking; manage maintenance requests for owned properties. |
| **Admin / Moderator** | Review reported listings, verify owner identity / property inspection **through manual checkboxes**, approve/revoke listings, and dismiss or act on scam reports. |

### Guided end-to-end test

1. Register **one landlord** and **one student** (separate browser profiles help).
2. Landlord creates a complete property listing. New or edited listings start unapproved.
3. Admin opens `/admin`, records actual completed owner-document and inspection checks, then approves the listing. **Checking these boxes represents a manual reviewer action, not automated government or on-site verification.**
4. Student opens **Find Housing**, filters by area/budget, views property detail, and requests a visit.
5. Landlord opens **Landlord Dashboard**, schedules the visit, and student requests a simulated booking. Landlord confirms it. No money is charged or held.
6. Student can now submit a tenant-marked review. A non-confirmed student cannot review that property.
7. Another student reports the listing: it disappears from public search until admin review. Admin can dismiss the report (restore visibility if otherwise approved) or take it down.
8. Save a housing search as a student. When another matching listing is approved, the alert appears in **Profile**.
9. Use **Roommates** to request a connection; the other student must approve before protected contact information is revealed. Profile visibility can be turned off.
10. Open **Mess Manager** as a student, create a private group, share its join code with members, and record meal and expense entries. See month-specific per-member summary and balances.

## 3. Features mapped to the brief

1. **Owner listings:** rent, deposit, utilities, facilities, gender rules, photo URLs, geographic location, availability date, owner operations.
2. **Search/filter/map:** area, distance, budget, property type, facilities, gender; map location search for Bangladesh, including Bogura.
3. **Listing verification:** admin manually checks owner identity and inspection status, then grants approval; owner edits reset approval.
4. **Roommate profiles:** lifestyle, budget, area, habits and privacy visibility.
5. **Compatibility:** explained scores and contact sharing after mutual acceptance.
6. **Visit/booking:** student request → landlord scheduling → student booking request → landlord confirmation; simulated records only.
7. **Reviews:** only students with a landlord-confirmed booked record can review. This is an **application-level eligibility proxy**, not third-party physical residency certification.
8. **Scam reports:** newly reported listings are hidden pending admin review; administrator can dismiss or remove.
9. **Shared expense management:** private mess groups, join codes, meals, bazaar/utility costs, monthly summaries and balances.
10. **Maintenance and alerts:** booked tenants submit maintenance for the booked property; the owner updates status. Saved searches generate in-app alerts when matching listings are approved.

**Innovations beyond the minimum requirements**

- **Side-by-side property comparison:** up to three approved properties per signed-in user (`/compare`).
- **Total monthly living cost & budget fit:** interactive calculation of rent, food, utilities, transportation and other expenses (`/living-cost`). The figures are **user-provided estimates**, not guaranteed rates or predictions.

See [`docs/REQUIREMENTS_MATRIX.md`](docs/REQUIREMENTS_MATRIX.md) for scope, limitations, and evidence.

## 4. Translation and user data

The UI supports **English** and **বাংলা**. Built-in interface text and known sample housing and roommate content are localized. Owners can provide an optional Bengali listing title and description. **New user-authored free-text content is intentionally shown as written**; arbitrary text is not machine-translated without consent/translation service. Map search supports familiar Bangla and English place-name forms where the geocoding service recognizes them.

## 5. Repository guide

```
SmartRent_BD/
├─ main.py                      # Application routes, templates, access protection
├─ app/
│  ├─ auth.py                   # Password/session utilities
│  ├─ auth_routes.py            # Login/registration/logout
│  ├─ database.py               # Safe schema creation and migrations
│  ├─ features.py               # Booking, alerts, compare, living cost, private mess
│  ├─ landlord_routes.py        # Owner-only APIs
│  ├─ i18n.py                   # UI translation helpers
│  └─ ...                       # Listing/localization/location helpers
├─ templates/                   # Jinja HTML pages
├─ static/                      # CSS and client JS
├─ tests/                       # Isolated application tests
├─ docs/                        # Submission and verification material
├─ requirements.txt
├─ requirements-dev.txt
├─ run.bat                       # Windows setup and launcher
└─ setup_admin.py               # Explicit local admin setup
```

**SQLite:** database tables are created/updated on app startup without wiping existing data. The provided ZIP may include an **existing local dataset** to let its owner open it as-is. `.gitignore` intentionally blocks `smartrent.db`, `smartrent_backup.db`, `.env`, and `.venv` from GitHub. The hosted GitHub repository starts with a **fresh empty database** and newly registered accounts: never upload someone else's emails, phone numbers, session tokens, or real IDs. If you need an organizer demo dataset, create synthetic records and document it separately.

**DO NOT run** `seed_data.py` for normal startup: it is a sample-data reset utility and demands deliberate command-line confirmation and a second interactive confirmation when an existing DB is present.

## 6. Run tests

```bash
pip install -r requirements.txt -r requirements-dev.txt
python -m pytest -q tests
```

Tests use separate temporary databases; they do **not** mutate your current `smartrent.db`. See [`docs/QA_RESULTS.md`](docs/QA_RESULTS.md) for coverage and remaining manual checks.

## 7. Important boundaries

- **No real payments, escrow, refunds, landlord ID API, on-site inspection service, legal registration or guaranteed rental agreement.** Agreement is a downloadable/printable *draft*, requiring independent review. Any verification status is from a moderator's manual attestation.
- **Use HTTPS, secure session-cookie configuration, rate limiting, production secrets, privacy/legal review, real ID verification and managed database backups before public Internet deployment.** Local hackathon run is not equivalent to production security certification.
- **Maps:** external geocoding/OSM needs Internet. A searched place on the map does not mean a verified property is available there. Listing pins come from approved/unflagged property data.
- **External photos:** housing images are illustrative or landlord-supplied URLs. Do not mistake them for inspection evidence.
- **Browser QA:** automated API/template tests passed in the authoring environment; interactive browser end-to-end testing and external map/geocoder availability should be checked on a real local Windows browser before submission.

## 8. Submission

See [`docs/SUBMISSION_CHECKLIST.md`](docs/SUBMISSION_CHECKLIST.md) for GitHub source/video/docs submission. **Deadline: October 28, 2026 at 8:00 AM Bangladesh time**. After submitting, **feature freeze** applies: fixes and UI/UX improvement allowed, but no new features or changes to core functionality.

**SmartRent BD — PUB CSE FEST 2026 team project.**
