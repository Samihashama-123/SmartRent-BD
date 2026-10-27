# C3. SmartRent BD — Requirements Coverage

The feature list below follows the organizer-supplied C3 project brief. "Supported" means an implemented workflow with application-level validation. It does not imply external verification of a physical property or payment service.

| # | Mandatory requirement | Implemented workflow / evidence | Important qualification |
|---|---|---|---|
| 1 | Listings with rent, deposit, utilities, amenities, photos, gender, map location, availability | Landlord dashboard creates/edits/archives owned property; `app/landlord_routes.py`, `templates/landlord.html` | Owner-submitted photos and geolocation require independent verification. |
| 2 | Search/filter + map | `/listings`; area, campus, distance, budget, type, facilities, policy, map location search | Map geocoding uses external network; only published/approved properties are public. |
| 3 | Verify owner identity & inspect listing; admin marks verified | `/admin` manual identity/inspection checklist plus approve/revoke; `app/features.py`, `main.py` | **Manual reviewer attestations**, not integration with any government ID/inspection provider. |
| 4 | Roommate profile | `/roommates`; preferences for budget, area, sleep, study, cleaning, smoking, food, guests and visibility | Self-reported habits. |
| 5 | Compatibility score & explanation, mutual contact | Matching score and reasons, request → accept/decline, restricted phone before acceptance | Rules-based scoring, not trained ML; visibility option. |
| 6 | Visit and booking | Student visit request → landlord schedule → student booking request → landlord confirmation | No actual deposit/payment. Booking is a stored simulated record. |
| 7 | Tenant-only reviews | `/api/submit-review` checks confirmed booking; nonbooked cannot submit; duplicate review blocked | Verified within this app by landlord-confirmed booking, not by physical residence proof. |
| 8 | Report fraud; hide listing until review | `/api/report-listing` immediately flags and hides; admin dismiss/takedown action | Admin should review promptly; reporting can be abused, so audit/rate-limit before production. |
| 9 | Utility split, meals, balances, monthly summary | Private join-code mess groups; `/mess-manager` member meal/expense entries and month-filtered summary | Internal book-keeping; no real money transfers or payment reconciliation. |
| 10 | Maintenance to owner + saved search alerts | Booked tenant's maintenance tickets with landlord status; Profile in-app alerts triggered on matching listing approval | Alerts are **in-app**, not push/email. Pending listing approval does not alert students. |

## Innovations

- **Compare up to 3 homes** (`/compare`) with normalized property facts and links to total cost.
- **Total Monthly Living Cost + Budget Fit** (`/living-cost`): user-adjusted rent, meals, utilities, transportation, other monthly costs, compared to budget.

## Existing optional features

- **Fair Rent Estimation:** rules-based estimate (`/fair-rent`), not artificial intelligence prediction.
- **Rental Agreement Draft:** bilingual print-friendly draft (`/agreement`), not stamped/legally certified paperwork.

## Risks / further work for public deployment

- Real independent owner identity checks and documented inspection evidence.
- Deployment-grade security hardening: HTTPS, CSRF configuration and session cookie settings, account lockout/rate limiting, trusted file hosting, monitoring and backup.
- Legal review of rental agreement terms, content/moderation policy, consent, privacy and user data storage.
- Real tenant residence attestation rather than booking-only review eligibility.
- Performance and full cross-browser/manual accessibility verification.

These items must **not** be represented as completed capabilities in a presentation.
