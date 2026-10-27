# Quality Assurance — Implemented Test Evidence

The project includes a portable automated test suite in `tests/test_core_workflows.py`.

### How to reproduce

```bash
pip install -r requirements.txt -r requirements-dev.txt
python -m pytest -q tests
```

**Recorded automated result (October 26, 2026):** 4 pytest tests passed with 2 framework-deprecation warnings. Each test creates a temporary isolated SQLite database, creates synthetic users, and exercises the FastAPI app directly. An additional local manual integration harness performed 61 checks using a separate copy of an existing SQLite dataset; this developer harness is not bundled because its absolute paths and data assumptions were environment-specific.

### Scenarios covered by automated API/template tests

- Page rendering and language switching in English and Bengali (including independent Student/Landlord/Admin access).
- Admin checklist before approval and saved-search alert on eligible property publication.
- New property approval checks and private property modification permissions.
- Student visit requests, landlord scheduling, simulated booking request, landlord confirmation.
- Review denied before confirmed booking, allowed afterward, and duplicate denied.
- Scam reports make the listing disappear from public results; dismissal restores eligible listings.
- Maintenance request restricted to a confirmed booked tenant and landlord ownership.
- Property comparison selection; monthly living cost page.
- Private mess group creation/join and month-based records.
- Python import/compilation and Jinja template parsing.
- JavaScript syntax checked in generated page scripts using Node.js in the test environment.

### Browser testing limitation

The authoring environment blocked localhost navigation from Playwright with `net::ERR_BLOCKED_BY_ADMINISTRATOR`. Consequently, **live browser click-through, complete responsive screenshots and external map/geocoder behavior have not been certified**. You should verify these in Chrome/Edge after extracting the ZIP, using the real Windows launch steps, before recording/submitting.

### Remaining checks before public deployment

This is a functional **local hackathon web application**, not a production security audit. Public deployment needs TLS, privacy/legal review, spam/abuse controls, rate limiting, controlled media upload, secure cookies and a managed database with backups. Manual identity and property inspection are not automated government-verified services. Billing and agreements do not transfer money or create legally validated contracts.

### Usability refinement, October 26, 2026

- Added session-scoped `/my-bookings` and an accessible read-only booking progress page.
- Added explicit visit-to-booking steps to property detail pages and booking help to search results.
- Added navigation back links and a maintenance empty-state call to action.
- Verified input prefix layout in a standalone Chromium CSS harness (`padding-left: 55px`).
- Re-ran temporary-database workflow tests: 4 tests passed.
- The original bundled `smartrent.db` hash is unchanged.

Browser navigation to localhost remained blocked; page-level visual QA is required on Windows.
