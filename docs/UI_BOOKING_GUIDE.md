# SmartRent BD — UI and Booking Guide (October 26, 2026)

## Student journey (বাংলা)

1. **বাসা খুঁজুন** (`/listings`) থেকে পছন্দের বাসার **দেখুন ও বুকিং করুন** চাপুন।
2. Property Details-এ **ভিজিটের অনুরোধ পাঠান** চাপুন। পছন্দের তারিখ ও সময় দিয়ে অনুরোধ জমা দিন।
3. মালিক নিজের **Landlord Dashboard → Visit & Booking Requests**-এ অনুরোধ দেখবেন, ভিজিটের সময় ঠিক করে দেবেন।
4. Student **আমার ভিজিট ও বুকিং** (`/my-bookings`) থেকে Status দেখতে পারবেন। `Visit scheduled` হলে আবার Property Details-এ গিয়ে **বুকিংয়ের অনুরোধ পাঠান** চাপবেন।
5. মালিকের Dashboard-এ নতুন Booking Request গেলে তিনি **Confirm booking** চাপবেন।
6. Status `Booked` হলে Student Maintenance Request এবং Tenant Review দিতে পারবেন।

**নোট:** এখানে কোনো বাস্তব অর্থ লেনদেন বা স্বয়ংক্রিয়ভাবে আইনি চুক্তি সম্পন্ন হয় না। মালিক ও বাসা ব্যক্তিগতভাবে যাচাই করুন।

## Owner journey

Sign in with a landlord account → Landlord Dashboard → `Visit & Booking Requests` → schedule a visit. After the student requests booking, return there to confirm or decline.

## New navigation and clarity improvements

- A **Go back / পেছনে যান** bar appears on inner pages. If the browser has an eligible previous page in this app, it goes back; otherwise its link navigates to a safe fallback.
- A read-only **My visits & bookings** page shows the currently authenticated student's requests only; it does not modify the database.
- Listing cards link clearly to a details page where the visit/booking process is described.
- Maintenance shows an actionable explanation instead of an unexplained empty dropdown when no confirmed bookings exist.
- The monthly cost calculator uses a specifically scoped currency-input layout so the `৳` prefix does not cover numeric input.

## Data safety / updating an existing installation

1. Exit the server (`Ctrl+C`) and save a copy of `smartrent.db`.
2. To preserve accounts created after your last download, apply the **source-only update ZIP** over your current `SmartRent_BD` directory. **Do not replace `smartrent.db`** with an older bundled database.
3. Run `python -m pytest -q tests` if dev dependencies are installed, or run `python -m uvicorn main:app --reload --port 8000` after activating the virtual environment.
4. Refresh Chrome with `Ctrl+Shift+R` to ensure the new stylesheet is loaded.

## Validation limits

The updated app was tested through Jinja template parsing, isolated-database FastAPI workflow tests and a Chromium standalone CSS layout check of currency inputs. End-to-end browsing of the localhost app was blocked by the test environment and must be verified on the actual Windows host.
