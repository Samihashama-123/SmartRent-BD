# v6 fixes (October 27, 2026)

- Admin sign-in defaults to admin dashboard; one login form for all roles, staff-friendly `/admin/login` link.
- Landlord and admin menus contain only the services they can use, on desktop/mobile/home/footer. Student-only tools also block landlord access on the server.
- Property security notice icon and text now have independent columns, full BN/EN text.
- SMTP reset is enabled via a private `.env` loaded with `python-dotenv`. Real delivery **requires** SMTP credentials and a sender; it is not faked.
- No database schema or contents altered by this source-only update.
