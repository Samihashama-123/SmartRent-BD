
# 🏠 SmartRent BD

### Student Housing & Roommate Matching Platform

**PUB CSE FEST 2026 — Hackathon Project**

**Team Name:** SyntaxSpark

**Project Repository:** https://github.com/Samihashama-123/SmartRent-BD

---

## 🎬 Project Demo Video

Watch our SmartRent BD hackathon project demonstration:

### ▶️ [Watch SmartRent BD Demo Video on YouTube](https://youtu.be/o-poqv7qJtk)

**Video Link:** https://youtu.be/o-poqv7qJtk

---

## 📌 About SmartRent BD

SmartRent BD is a working, locally hosted full-stack web application designed to simplify student housing and roommate matching in Bangladesh.

The platform connects university students searching for accommodation with landlords offering rental properties. It also provides tools to help students compare housing options, find compatible roommates, manage shared expenses, and communicate with landlords.

SmartRent BD includes separate interfaces and workflows for Students, Landlords, and Administrators.

The application uses SQLite for persistent data storage and session-based authentication.

**Note:** SmartRent BD is a hackathon prototype. It does not process real payments.

---

## 🛠️ Technology Stack

| Component | Technology |
|-----------|------------|
| Backend | Python 3.11+, FastAPI |
| Frontend | HTML, CSS, JavaScript |
| Template Engine | Jinja2 |
| Database | SQLite |
| Authentication | Session-Based Authentication |
| Maps | Leaflet.js, OpenStreetMap |
| Email Recovery | SMTP (Optional Configuration) |
| Testing | Pytest |
| Development Environment | VS Code |

**Internet Requirement:** An internet connection is required for externally hosted map tiles, geocoding services, icon fonts, and some image assets.

---

## 🚀 1. Installation and Quick Start

### Windows / VS Code

**Step 1: Download the Project**

Download the repository as a ZIP file from GitHub and extract it, or clone it using Git:

```bash
git clone https://github.com/Samihashama-123/SmartRent-BD.git
```

**Step 2: Open the Project**

Open the `SmartRent-BD` project folder in Visual Studio Code.

**Step 3: Run the Application**

Double-click `run.bat`, or execute it from the VS Code terminal.

The script prepares the Python virtual environment, installs the required dependencies, and starts the application.

Alternatively, run the following commands manually:

```bash
python -m venv .venv
```

Activate the virtual environment.

For Windows Command Prompt:

```bash
.venv\Scripts\activate
```

For Git Bash:

```bash
source .venv/Scripts/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Start the server:

```bash
python -m uvicorn main:app --reload --port 8000
```

**Step 4: Open the Website**

Visit:

http://127.0.0.1:8000/

You can browse public housing listings before signing in.

**Step 5: Create an Account**

Register as a Student or Landlord to access role-specific features.

**Step 6: Stop the Server**

Press `Ctrl + C` in the terminal.

### Alternative Setup (macOS / Linux)

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m uvicorn main:app --reload --port 8000
```

---

## 🔐 2. User Roles and Authentication

SmartRent BD supports three primary user roles.

### 👨‍🎓 Student / Tenant

Students can:

- Register and manage their profiles.
- Browse approved housing listings.
- Search and filter properties.
- View property details and locations.
- Request property visits.
- Submit simulated booking requests.
- View booking status.
- Submit reviews after confirmed bookings.
- Search for compatible roommates.
- Send and accept roommate requests.
- Manage shared mess expenses.
- Report suspicious property listings.
- Submit maintenance requests.
- Save housing searches and receive in-app alerts.
- Compare available properties.
- Calculate estimated monthly living costs.

### 🏡 Landlord / Property Owner

Landlords can:

- Register and manage their accounts.
- Create housing listings.
- Add property descriptions, rent, deposit, facilities, and images.
- Set property locations.
- Update existing property information.
- View student visit requests.
- Schedule property visits.
- Approve or decline booking requests.
- Manage maintenance requests for their properties.

New or edited property listings require administrator approval before becoming publicly available.

### 🛡️ Administrator / Moderator

Administrators can:

- Access the Admin Dashboard.
- Review submitted property listings.
- Record manual owner-document checks.
- Record manual property-inspection checks.
- Approve or revoke listings.
- Review reported property listings.
- Dismiss reports or remove suspicious listings.
- Moderate property visibility.

**Important:** The verification process uses manual administrator checkboxes. It does not provide automated government identity verification or real-world inspection services.

### Administrator Account Setup

After installing dependencies, execute:

```bash
python setup_admin.py
```

Follow the terminal instructions to create an administrator account or set its password.

**Admin Login:** `/admin/login`

**Admin Dashboard:** `/admin`

Never publish administrator passwords or other private credentials.

### Password Recovery

SmartRent BD supports optional email-based password recovery through SMTP.

SMTP credentials must be configured privately in a local `.env` file.

See:

[Role-Based Navigation, Login and Email Recovery Guide](docs/FINAL_LOGIN_NAV_EMAIL_v6.md)

---

## 🏠 3. Core Features

### 3.1 Property Listing Management

Landlords can create and manage property listings containing:

- Property title and description
- Monthly rent
- Security deposit
- Utility information
- Property type
- Available facilities
- Gender preferences or rules
- Property photographs
- Availability date
- Geographic location

New and edited listings remain unapproved until reviewed by an administrator.

### 3.2 Advanced Property Search and Maps

Students can search for suitable accommodation using:

- Location and area
- Rental budget
- Property type
- Facilities
- Gender-related preferences
- Distance and geographic location

Property locations are displayed using Leaflet and OpenStreetMap.

Location search supports Bangladesh, including Bogura, subject to the external geocoding service.

### 3.3 Property Verification

The administrator reviews listings before publication.

The workflow includes:

1. Landlord submits a listing.
2. Listing remains pending.
3. Administrator reviews listing information.
4. Administrator records manual verification checks.
5. Administrator approves or rejects the listing.
6. Approved listings become publicly visible.

Manual verification indicators do not guarantee that an actual on-site inspection or government identity check has occurred.

### 3.4 Roommate Matching

Students can create roommate profiles using information such as:

- Budget
- Preferred location
- Lifestyle preferences
- Daily habits
- Personal preferences

The platform calculates compatibility scores based on profile information.

Students can send roommate connection requests.

Protected contact details are revealed only after the required mutual acceptance.

Profile visibility can also be controlled.

### 3.5 Visit and Booking Management

The visit and booking workflow is:

1. Student discovers a property.
2. Student requests a property visit.
3. Landlord schedules the visit.
4. Student submits a booking request.
5. Landlord approves or declines the booking.
6. Student views the updated booking status.

All bookings are simulated application records.

**No real payment is collected or processed.**

### 3.6 Tenant Reviews

Students can submit property reviews after a landlord-confirmed booking.

Students without a qualifying confirmed booking cannot submit a review for that property.

This is an application-level eligibility check, not independent confirmation of physical residency.

### 3.7 Scam Reporting

Students can report suspicious property listings.

A newly reported listing is hidden from public search while awaiting administrator review.

The administrator can:

- Review the submitted report.
- Dismiss the report.
- Restore a listing when appropriate.
- Remove or revoke a suspicious listing.

### 3.8 Shared Mess Expense Manager

Students can create private mess groups and manage shared expenses.

Supported activities include:

- Creating a mess group
- Joining through a private join code
- Managing group members
- Recording meals
- Recording bazaar expenses
- Tracking utility and shared costs
- Viewing monthly summaries
- Calculating individual balances

### 3.9 Maintenance Requests

Eligible tenants can submit maintenance requests related to their booked properties.

Landlords can review these requests and update their status.

### 3.10 Saved Search and Notifications

Students can save housing search preferences.

When newly approved listings match their saved preferences, the platform generates in-app alerts.

These notifications can be viewed through the student's profile.

---

## 💡 4. Additional Innovative Features

Beyond the core hackathon requirements, SmartRent BD includes additional student-focused tools.

### 4.1 Side-by-Side Property Comparison

Students can compare up to three approved properties.

Comparison helps users evaluate housing choices using available property information.

**Page:** `/compare`

### 4.2 Monthly Living Cost Calculator

Students can estimate their total monthly living expenses.

The calculation can include:

- House rent
- Food expenses
- Utilities
- Transportation
- Other expenses

The tool helps students understand their estimated monthly budget before choosing accommodation.

**Page:** `/living-cost`

All values are user-provided estimates, not guaranteed prices or financial predictions.

### 4.3 Fair Rent Estimator

SmartRent BD includes a rule-based Fair Rent Estimator.

It provides an indicative rent estimate based on the available input factors.

**Page:** `/fair-rent`

This is not an AI prediction or a certified property valuation.

### 4.4 Rental Agreement Draft

The platform provides a rental agreement draft to help organize basic rental terms.

**Page:** `/agreement`

Generated agreements are drafts only. They are not automatically registered or legally certified.

---

## 🌐 5. Bilingual Interface

SmartRent BD supports:

- English
- বাংলা (Bangla)

The application includes translated interface text and localized sample content.

Landlords can optionally provide Bengali listing titles and descriptions.

New user-written content remains in its original language unless a translation is explicitly provided.

Some map searches support familiar Bangla and English place names when recognized by the geocoding service.

---

## 🧪 6. Guided End-to-End Testing

The following workflow can be used to demonstrate the application.

**Test 1: Registration**

Register one Student and one Landlord using separate browser profiles.

**Test 2: Property Submission**

The Landlord creates a complete property listing.

The listing initially remains unapproved.

**Test 3: Admin Approval**

The Administrator reviews the submitted listing, records any completed manual checks, and approves it.

**Test 4: Housing Search**

The Student searches for the approved property using available filters and opens its details.

**Test 5: Visit and Booking**

The Student requests a visit.

The Landlord schedules the visit.

The Student sends a booking request.

The Landlord confirms the booking.

**Test 6: Property Review**

The Student submits a review after the confirmed booking.

**Test 7: Scam Reporting**

Another Student reports a listing.

The listing is hidden pending administrator review.

**Test 8: Saved Search Notifications**

A Student saves search preferences and receives an in-app alert when a newly approved listing matches them.

**Test 9: Roommate Matching**

Student A sends a roommate request.

Student B accepts the request.

Protected contact information becomes available after acceptance.

**Test 10: Mess Management**

A Student creates a mess group.

Another Student joins using the group code.

Members add meal and expense records and review monthly summaries.

For additional testing details, see:

[QA Results](docs/QA_RESULTS.md)

[Requirements Matrix](docs/REQUIREMENTS_MATRIX.md)

---

## 📁 7. Project Structure

```text
SmartRent_BD/
|
|-- main.py
|
|-- app/
|   |-- auth.py
|   |-- auth_routes.py
|   |-- database.py
|   |-- features.py
|   |-- landlord_routes.py
|   |-- matching.py
|   |-- estimator.py
|   |-- location_search.py
|   |-- content_localization.py
|   |-- i18n.py
|
|-- templates/
|   |-- index.html
|   |-- auth.html
|   |-- admin.html
|   |-- landlord.html
|   |-- listings.html
|   |-- listing_detail.html
|   |-- roommates.html
|   |-- mess_manager.html
|   |-- mess_workspace.html
|   |-- compare.html
|   |-- living_cost.html
|   |-- fair_rent.html
|   |-- agreement.html
|   |-- maintenance.html
|   |-- profile.html
|   |-- my_bookings.html
|   |-- password_recovery.html
|   |-- ...
|
|-- static/
|   |-- product.css
|   |-- product.js
|   |-- ui_polish.css
|   |-- ui_translate.js
|
|-- tests/
|   |-- test_core_workflows.py
|   |-- test_final_role_email_ui.py
|   |-- test_guest_roles_recovery.py
|   |-- test_photo_upload.py
|   |-- test_ui_ux_v9.py
|
|-- docs/
|   |-- DEMO_VIDEO_SCRIPT.md
|   |-- REQUIREMENTS_MATRIX.md
|   |-- QA_RESULTS.md
|   |-- SUBMISSION_CHECKLIST.md
|   |-- UI_BOOKING_GUIDE.md
|   |-- ...
|
|-- README.md
|-- START_HERE.md
|-- QA_RESULTS.md
|-- requirements.txt
|-- requirements-dev.txt
|-- setup_admin.py
|-- seed_data.py
|-- run.bat
|-- run.sh
|-- .env.example
|-- .gitignore
```

---

## 🗄️ 8. Database and Privacy

SmartRent BD uses SQLite.

Database tables are created or updated during application startup without intentionally wiping existing data.

The GitHub repository intentionally excludes the local application database.

The `.gitignore` file protects sensitive local files, including:

```gitignore
.env
.venv/
smartrent.db
smartrent_backup.db
*.sqlite
*.sqlite3
uploads/
```

The public repository does not contain the private local database used during development.

A new installation starts with its own local database and newly created user accounts.

**Do not upload:**

- Real passwords
- SMTP App Passwords
- Private `.env` configuration
- Personal user information
- Session tokens
- Real identity documents
- Private uploaded files

An `.env.example` file may be used to document configuration variable names without including real credentials.

**Important:** `seed_data.py` is a sample-data reset utility. Do not run it during normal startup.

---

## ✅ 9. Run Automated Tests

Install development dependencies:

```bash
pip install -r requirements.txt -r requirements-dev.txt
```

Run the automated tests:

```bash
python -m pytest -q tests
```

The test suite uses separate temporary databases and is designed not to modify the main local database.

Additional test coverage and verification notes are documented in:

[QA Results](docs/QA_RESULTS.md)

---

## ⚠️ 10. Important Limitations

SmartRent BD is a functional hackathon prototype designed primarily for local demonstration.

Current boundaries include:

- No real payment processing
- No real escrow or refund system
- No government identity verification API
- No automated physical property inspection
- No legal registration service
- No guaranteed rental agreement
- No production security certification

Administrator verification is performed through a manual moderation workflow.

Rental agreements generated by the application are drafts and require independent review.

Before production deployment, the application would require additional measures such as HTTPS, secure session configuration, rate limiting, production secret management, privacy review, and managed database backups.

Maps and geocoding rely on external services and internet availability.

Housing photos may be illustrative or landlord-provided. They should not be treated as independent inspection evidence.

---

## 📚 11. Project Documentation

Additional project documentation is available below:

- [Getting Started](START_HERE.md)
- [Requirements Matrix](docs/REQUIREMENTS_MATRIX.md)
- [QA Results](docs/QA_RESULTS.md)
- [Demo Video Script](docs/DEMO_VIDEO_SCRIPT.md)
- [Role-Based Login and Email Recovery](docs/FINAL_LOGIN_NAV_EMAIL_v6.md)
- [UI and Booking Guide](docs/UI_BOOKING_GUIDE.md)
- [Submission Checklist](docs/SUBMISSION_CHECKLIST.md)

---

## 🏆 12. Hackathon Submission

**Event:** PUB CSE FEST 2026

**Team:** SyntaxSpark

**Project:** SmartRent BD

**Category:** Student Housing & Roommate Matching Platform

**GitHub Repository:**

https://github.com/Samihashama-123/SmartRent-BD

**Project Demonstration Video:**

https://youtu.be/o-poqv7qJtk

**Submission Deadline:** October 28, 2026, at 8:00 AM (Bangladesh Time).

After submission, the project follows the hackathon feature-freeze requirements. Bug fixes and UI/UX improvements may be allowed, but new features or changes to core functionality should not be introduced.

---

## ❤️ Team SyntaxSpark

**SmartRent BD — Making Student Housing Search and Roommate Matching Simpler in Bangladesh.**

Developed for **PUB CSE FEST 2026**.
