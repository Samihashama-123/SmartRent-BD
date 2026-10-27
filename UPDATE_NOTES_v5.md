# SmartRent BD v5 — Navigation, Guest & Account Recovery

Updated from v4. Changes:

1. Public homepage and approved listing browsing (without login).
2. Separate Student, Landlord and Admin desktop/mobile navigation, footer, and home cards.
3. Server-side authorization and bilingual permission screen for wrong-role pages.
4. **Forgot Password** link with genuine, expiring, one-use email reset flow. SMTP integration requires setup; no false success if not configured.
5. Property Detail map behind the sticky header; More tools dropdown size bounded to viewport.
6. Guest sign-in prompts on private listing actions, with safe return-to-page on login.
7. Template, functional and new permission/forgot-password tests.

Limitations: SMTP send needs real credentials and deployment URL; external map imagery and all mobile interactions still need browser checking. None of the user database tables are deleted.
