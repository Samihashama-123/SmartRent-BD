# Start Here — SmartRent BD

1. Windows: double-click `run.bat` to create a Python virtual environment and start the website.
2. Open `http://127.0.0.1:8000/` to browse homes without logging in. Sign in only when you need a private service.
3. Register a student or landlord account. For admin credentials run `python setup_admin.py` in the project root, then open `/admin/login`.
4. Read `README.md` for complete workflows and environment requirements.
5. For visit/booking steps, read `docs/UI_BOOKING_GUIDE.md`.
6. For real Forgot Password email, copy `.env.example` to a private `.env`, enter verified SMTP settings and restart. Without provider credentials no reset email can arrive. See `docs/FINAL_LOGIN_NAV_EMAIL_v6.md`.
7. Before PUB CSE FEST 2026 submission, follow `docs/SUBMISSION_CHECKLIST.md`.

**Do not run `seed_data.py` as part of startup; it can intentionally replace local data after explicit confirmations.** No real payments or automatic legal/government verification take place.
