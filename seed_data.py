import json
import sqlite3
import os
from app.database import DB_PATH, init_db

def seed():
    # DANGEROUS/OPT-IN sample reset. Never delete someone's database implicitly.
    import sys
    if '--confirm-replace-sample-database' not in sys.argv:
        raise SystemExit(
            "Sample data generator is OPT-IN and replaces the database. "
            "Back up your data, then run: python seed_data.py "
            "--confirm-replace-sample-database"
        )
    if os.path.exists(DB_PATH):
        response = input('Replace existing database and ALL data? Type REPLACE: ').strip()
        if response != 'REPLACE':
            raise SystemExit('Cancelled. No database changes made.')
        os.remove(DB_PATH)

    init_db()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # 1. Users
    users_data = [
        # id=1: Default Student Persona (Tanvir)
        ("Tanvir Ahmed", "tanvir.buet@gmail.com", "+880 1711-234567", "student", 
         "https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=150&auto=format&fit=crop&q=80", 
         1, "BUET", "Computer Science & Engineering", "2005089", 
         "3rd year CSE student. Quiet, focused on coding and competitive programming. Loves clean surroundings and coffee."),
        
        # id=2: Student (Nusrat)
        ("Nusrat Jahan", "nusrat.bracu@gmail.com", "+880 1822-345678", "student", 
         "https://images.unsplash.com/photo-1544005313-94ddf0286df2?w=150&auto=format&fit=crop&q=80", 
         1, "BRAC University", "Pharmacy", "21101432", 
         "Pharmacy major at BRACU. Looking for safe female accommodation near Merul Badda / Mohakhali."),
        
        # id=3: Student (Sadman)
        ("Sadman Sakib", "sadman.nsu@gmail.com", "+880 1933-456789", "student", 
         "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=150&auto=format&fit=crop&q=80", 
         1, "North South University (NSU)", "BBA / Finance", "2221567", 
         "Active student, plays football, studies during evenings. Budget around 6k-8k."),

        # id=4: Student (Ayesha)
        ("Ayesha Siddiqua", "ayesha.du@gmail.com", "+880 1644-567890", "student", 
         "https://images.unsplash.com/photo-1517841905240-472988babdf9?w=150&auto=format&fit=crop&q=80", 
         1, "Dhaka University (DU)", "Economics", "DU-ECO-78", 
         "DU Master's student. Looking for a peaceful, well-lit study room near Azimpur or Katabon."),

        # id=5: Landlord Persona (Rafiqul Islam)
        ("Engr. Rafiqul Islam", "rafiqul.prop@gmail.com", "+880 1715-987654", "landlord", 
         "https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?w=150&auto=format&fit=crop&q=80", 
         1, "Ex-BUETian Landlord", "Property Management", "NID-1975269824", 
         "Verified landlord managing genuine, student-friendly bachelor apartments in Katabon, Dhanmondi, and Azimpur."),

        # id=6: Landlord (Alhaj Mokbul Hossain)
        ("Alhaj Mokbul Hossain", "mokbul.bashundhara@gmail.com", "+880 1819-112233", "landlord", 
         "https://images.unsplash.com/photo-1500648767791-00dcc994a43e?w=150&auto=format&fit=crop&q=80", 
         1, "Bashundhara Landlords Assoc", "Real Estate", "NID-1968112344", 
         "Owner of modern student hostels in Bashundhara R/A Block C & D, right next to NSU and IUB."),

        # id=7: Admin Persona (SmartRent Moderator)
        ("SmartRent BD Admin", "admin@smartrentbd.com", "+880 1300-000111", "admin", 
         "https://images.unsplash.com/photo-1535713875002-d1d0cf377fde?w=150&auto=format&fit=crop&q=80", 
         1, "SmartRent Verification Board", "Chief Inspector", "ADMIN-001", 
         "SmartRent BD Platform Verification Officer and Anti-Scam Response Lead.")
    ]

    cursor.executemany("""
    INSERT INTO users (name, email, phone, role, avatar, nid_verified, university, department, student_id, bio)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, users_data)

    # 2. Listings
    listings_data = [
        # Listing 1: Katabon near DU/BUET
        (5, "Bright 2-Seat Mess Room Near BUET & DU (Palashi Gate)",
         "Ideal accommodation for BUET/DU students! Spacious 2-bed room in a clean, quiet 4th floor bachelor apartment. Walkable distance (5 mins) to BUET Palashi gate and Katabon intersection. Filtered drinking water, superfast 50Mbps fiber Wi-Fi, inverter IPS backup for load-shedding, and an experienced Khala who cooks delicious healthy Bengali meals twice daily.",
         "Mess Seat", "House 24, Road 2, Katabon Dhal", "Katabon", "BUET & Dhaka University", 0.4,
         4200, 4200, "Includes Wi-Fi, Water & Khala. Electricity token split equally.",
         "Male Only", "2026-11-01",
         json.dumps([
             "https://images.unsplash.com/photo-1555854877-bab0e564b8d5?w=800&auto=format&fit=crop&q=80",
             "https://images.unsplash.com/photo-1595526114035-0d45ed16cfbf?w=800&auto=format&fit=crop&q=80",
             "https://images.unsplash.com/photo-1586023492125-27b2c045efd7?w=800&auto=format&fit=crop&q=80"
         ]),
         23.7381, 90.3888,
         json.dumps(["wifi", "generator", "water_247", "meals", "attached_bath", "cctv"]),
         1, 0, None, 142),

        # Listing 2: Bashundhara R/A near NSU & IUB
        (6, "Premium AC Single Room with Balcony (Block C - 2 min to NSU)",
         "High-spec single room with attached washroom and private balcony in Bashundhara Block C. 200 meters walk from North South University Gate 8 and IUB. Comes furnished with study desk, ergonomic chair, wardrobe, and single bed with mattress. Full IPS backup runs fan + lights + Wi-Fi router. 24/7 lift, guard, and fingerprint entry lock for maximum security.",
         "Single Room", "Plot 182, Road 4, Block C, Bashundhara R/A", "Bashundhara R/A", "North South University (NSU)", 0.3,
         11500, 15000, "Wi-Fi, WASA, Maid service included. Electricity prepaid card meter.",
         "Any", "2026-11-05",
         json.dumps([
             "https://images.unsplash.com/photo-1522771739844-6a9f6d5f14af?w=800&auto=format&fit=crop&q=80",
             "https://images.unsplash.com/photo-1502672260266-1c1ef2d93688?w=800&auto=format&fit=crop&q=80",
             "https://images.unsplash.com/photo-1560448204-e02f11c3d0e2?w=800&auto=format&fit=crop&q=80"
         ]),
         23.8152, 90.4267,
         json.dumps(["wifi", "generator", "water_247", "attached_bath", "balcony", "lift", "cctv", "refrigerator"]),
         1, 0, None, 289),

        # Listing 3: Merul Badda near BRAC University
        (5, "Safe Female Student Mess Seat (Facing BRACU New Campus)",
         "Dedicated secure female student hostel/mess. Directly opposite BRAC University Merul Badda campus entrance. 24/7 female guard, CCTV in common corridor, biometric entry. Three hygienic home-cooked meals every day (breakfast, lunch, dinner). Quiet library room available for exam season studies.",
         "Hostel Seat", "Building 12, DIT Project, Merul Badda", "Mohakhali / Merul Badda", "BRAC University", 0.2,
         6800, 5000, "All inclusive: 3 daily meals, gas, electricity, high-speed Wi-Fi.",
         "Female Only", "2026-10-28",
         json.dumps([
             "https://images.unsplash.com/photo-1598928506311-c55ded91a20c?w=800&auto=format&fit=crop&q=80",
             "https://images.unsplash.com/photo-1505693416388-ac5ce068fe85?w=800&auto=format&fit=crop&q=80",
             "https://images.unsplash.com/photo-1540518614846-7ede433c4550?w=800&auto=format&fit=crop&q=80"
         ]),
         23.7712, 90.4239,
         json.dumps(["wifi", "generator", "water_247", "meals", "cctv", "refrigerator"]),
         1, 0, None, 310),

        # Listing 4: Dhanmondi near UIU / Daffodil / Dhaka College
        (5, "Complete 3-Bed Bachelor Flat for University Group (Dhanmondi 9/A)",
         "Ready-to-move spacious 1450 sqft 3-bed 3-bath flat for a group of 5-6 university students. Large drawing-cum-dining space, modern kitchen with piped gas connection, separate laundry area, two south-facing balconies. 24/7 security guard, CCTV, lift, dedicated car/bike parking. Landlord does not disturb tenants.",
         "Bachelor Flat", "House 67, Road 9/A, Dhanmondi", "Dhanmondi", "Dhanmondi Campuses / UIU / State Univ", 0.8,
         28000, 30000, "Service charge ৳4,000 includes security, lift, water, and trash.",
         "Male Only", "2026-11-15",
         json.dumps([
             "https://images.unsplash.com/photo-1600585154340-be6161a56a0c?w=800&auto=format&fit=crop&q=80",
             "https://images.unsplash.com/photo-1600566753190-17f0baa2a6c3?w=800&auto=format&fit=crop&q=80",
             "https://images.unsplash.com/photo-1600573472550-8090b5e0745e?w=800&auto=format&fit=crop&q=80"
         ]),
         23.7504, 90.3752,
         json.dumps(["wifi", "generator", "water_247", "attached_bath", "balcony", "lift", "cctv"]),
         1, 0, None, 195),

        # Listing 5: Farmgate near Coaching & Metro Station
        (6, "Affordable Single Room Sublet with Attached Bath (Tejgaon / Farmgate)",
         "Budget-friendly single room in a respectable family flat (sublet with separate private key). 3 minutes walking distance to Farmgate Metro Station. Quick commute to DU, Farmgate colleges, and Tejgaon industrial campus. Quiet environment suitable for BCS and university admission examinees.",
         "Single Room", "12/A East Tejturi Bazar, Farmgate", "Farmgate", "DU / Metro Route Campuses", 1.2,
         6200, 6000, "Electricity and gas shared. Wi-Fi free.",
         "Male Only", "2026-11-01",
         json.dumps([
             "https://images.unsplash.com/photo-1512918728675-ed5a9ecdebfd?w=800&auto=format&fit=crop&q=80",
             "https://images.unsplash.com/photo-1513694203232-719a280e022f?w=800&auto=format&fit=crop&q=80"
         ]),
         23.7570, 90.3912,
         json.dumps(["wifi", "water_247", "attached_bath"]),
         1, 0, None, 88),

        # Listing 6: Flagged Listing (Scam Demo for Anti-Scam Shield!)
        (6, "[SUSPICIOUS] Ultra Luxury Studio Flat near AIUB - Only 3000 BDT (Advance Mandatory)",
         "Full furnished 5-star studio near AIUB Kuril. AC, TV, Fridge, all free. Very low rent because I am living abroad. You MUST bKash send ৳3,000 booking fee to phone 01999999999 before I give you the key or show the flat. No visit allowed without advance deposit.",
         "Bachelor Flat", "Kuratoli, Kuril", "Kuril", "AIUB & American International University", 0.5,
         3000, 3000, "Everything free",
         "Any", "2026-10-25",
         json.dumps([
             "https://images.unsplash.com/photo-1502672260266-1c1ef2d93688?w=800&auto=format&fit=crop&q=80"
         ]),
         23.8210, 90.4190,
         json.dumps(["wifi", "generator", "meals"]),
         0, 1, "Reported by 3 students: Advance bKash extortion scam demanding cash before physical inspection.", 52)
    ]

    cursor.executemany("""
    INSERT INTO listings (
        owner_id, title, description, property_type, address, area, university_nearby,
        distance_km, rent_amount, deposit_amount, utilities_desc, gender_policy,
        availability_date, photos, lat, lng, facilities, is_verified, is_flagged, flag_reason, views_count
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, listings_data)

    # 3. Roommate Profiles
    roommate_data = [
        # Tanvir (User 1)
        (1, 3500, 6000, "Katabon / Palashi / Dhanmondi", "BUET / Dhaka University",
         "night_owl", "silent", "high", "non_smoker", "mess_food", "daytime_only",
         "Competitive programmer & AI enthusiast. Usually awake coding until 2:30 AM with headphones. Keeps room spotless.", 1),

        # Nusrat (User 2)
        (2, 5000, 8000, "Merul Badda / Rampura / Banani", "BRAC University",
         "early_bird", "silent", "high", "non_smoker", "self_cook", "no_guests",
         "Pharmacy student at BRACU. Clean, respectful of personal boundaries, prefers a focused academic atmosphere.", 1),

        # Sadman (User 3)
        (3, 4000, 6500, "Bashundhara R/A / Kuril", "North South University (NSU)",
         "night_owl", "group", "moderate", "non_smoker", "mess_food", "weekends_allowed",
         "BBA junior at NSU. Passionate about startups and gaming. Easygoing roommate who loves good food and chill weekends.", 1),

        # Ayesha (User 4)
        (4, 4500, 7000, "Azimpur / Lalbagh / Katabon", "Dhaka University (DU)",
         "early_bird", "silent", "high", "non_smoker", "mess_food", "daytime_only",
         "DU Economics research student. Enjoys reading, quiet mornings, and a disciplined mess study environment.", 1)
    ]

    cursor.executemany("""
    INSERT INTO roommate_profiles (
        user_id, budget_min, budget_max, preferred_area, preferred_university,
        sleep_schedule, study_habit, cleanliness, smoking, food_habit, guest_policy, hobbies, is_visible
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, roommate_data)

    # 4. Reviews on Listing 1
    cursor.execute("""
    INSERT INTO reviews (listing_id, student_id, rating, cleanliness_rating, owner_rating, facilities_rating, comment, is_verified_tenant)
    VALUES (1, 4, 5, 5, 5, 5, 'Lived in this Katabon mess for 8 months during my 2nd year. Engr. Rafiqul uncle is extremely cooperative, never enters without knocking, and the IPS saved us during exam nights!', 1)
    """)

    # 5. Sample Visit & Booking Request
    cursor.execute("""
    INSERT INTO visits_and_bookings (listing_id, student_id, owner_id, visit_date, time_slot, status, notes, simulated_deposit_paid, deposit_amount)
    VALUES (1, 1, 5, '2026-10-24', 'Evening (5:00 PM - 7:00 PM)', 'visit_scheduled', 'BUET student coming to check the south-facing window & study table.', 0, 0)
    """)
    cursor.execute("""
    INSERT INTO visits_and_bookings (listing_id, student_id, owner_id, visit_date, time_slot, status, notes, simulated_deposit_paid, deposit_amount)
    VALUES (2, 3, 6, '2026-10-20', 'Afternoon (2:00 PM - 4:00 PM)', 'booked', 'Visit completed on Oct 20. Token booking confirmed via simulated escrow.', 1, 1500)
    """)

    # 6. Maintenance Requests
    cursor.execute("""
    INSERT INTO maintenance_requests (listing_id, tenant_id, owner_id, category, title, description, priority, status)
    VALUES (1, 1, 5, 'Plumbing', 'Bathroom Cistern Valve Slow Leak', 'Water is dripping slowly from the main cistern pipe, causing floor wetness.', 'medium', 'in_progress')
    """)
    cursor.execute("""
    INSERT INTO maintenance_requests (listing_id, tenant_id, owner_id, category, title, description, priority, status)
    VALUES (2, 3, 6, 'Wi-Fi', 'Router 5GHz Band Dropping Frequency', 'The shared router on the 4th floor loses connection during rain.', 'low', 'open')
    """)

    # 7. Reports on Scam Listing
    cursor.execute("""
    INSERT INTO reports (listing_id, reporter_id, reason, details, status)
    VALUES (6, 3, 'Advance Payment Scam', 'The person on WhatsApp insisted on receiving ৳3,000 bKash cash-out before even revealing the flat door number. Refused physical visit.', 'pending')
    """)

    # 8. Mess Manager Data (Dhanmondi Shanti Nibash Mess)
    cursor.execute("""
    INSERT INTO mess_groups (name, address, monthly_rent)
    VALUES ('Dhanmondi Shanti Nibash Mess', 'House 41, Road 7/A, Dhanmondi', 24000)
    """)
    mess_id = cursor.lastrowid

    members = [
        (mess_id, "Tanvir Ahmed", "+880 1711-234567", 6000, 6000),
        (mess_id, "Sadman Sakib", "+880 1933-456789", 6000, 6000),
        (mess_id, "Fahim Shahriar", "+880 1822-111222", 6000, 6000),
        (mess_id, "Rafiul Karim", "+880 1633-444555", 6000, 6000)
    ]
    cursor.executemany("""
    INSERT INTO mess_members (mess_id, name, phone, seat_rent, deposit)
    VALUES (?, ?, ?, ?, ?)
    """, members)

    # Sample Bazaar entries
    bazaars = [
        (mess_id, "Tanvir Ahmed", 2400, "2026-10-18", "Chicken 4kg, Rui fish 2kg, Rice 25kg, Onions"),
        (mess_id, "Sadman Sakib", 1650, "2026-10-20", "Cooking Oil 5L, Potatoes, Green chili, Eggs 2 crates"),
        (mess_id, "Fahim Shahriar", 1950, "2026-10-22", "Beef 1.5kg, Garlic, Ginger, Lentils (Dal), Spices")
    ]
    cursor.executemany("""
    INSERT INTO mess_bazaar (mess_id, buyer_name, amount, bazaar_date, items_description)
    VALUES (?, ?, ?, ?, ?)
    """, bazaars)

    # Sample Utilities
    utilities = [
        (mess_id, "DESCO Electricity Prepaid Card", 2200, "October 2026", "Tanvir Ahmed"),
        (mess_id, "Khala (Maid & Cook) Monthly Bill", 3500, "October 2026", "Sadman Sakib"),
        (mess_id, "Carnival Fiber Internet (50 Mbps)", 1200, "October 2026", "Fahim Shahriar"),
        (mess_id, "WASA Water & Trash Bill", 900, "October 2026", "Rafiul Karim")
    ]
    cursor.executemany("""
    INSERT INTO mess_utilities (mess_id, title, amount, month, paid_by)
    VALUES (?, ?, ?, ?, ?)
    """, utilities)

    # Sample Meal counts for members
    cursor.execute("SELECT id FROM mess_members WHERE mess_id = ?", (mess_id,))
    member_ids = [row[0] for row in cursor.fetchall()]

    # 5 days of meals
    meal_records = []
    dates = ["2026-10-18", "2026-10-19", "2026-10-20", "2026-10-21", "2026-10-22"]
    for d in dates:
        for mid in member_ids:
            meal_records.append((mess_id, mid, d, 1.0, 1.0))
    cursor.executemany("""
    INSERT INTO mess_meals (mess_id, member_id, meal_date, lunch_count, dinner_count)
    VALUES (?, ?, ?, ?, ?)
    """, meal_records)

    conn.commit()
    conn.close()
    print("Database successfully seeded with realistic Bangladeshi campus records!")

if __name__ == "__main__":
    seed()
