
import sqlite3
import os


# ============================================================
# SMARTRENT BD — DATABASE CONFIGURATION
# ============================================================

BASE_DIR = os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)

DB_PATH = os.path.join(
    BASE_DIR,
    "smartrent.db"
)


# ============================================================
# DATABASE CONNECTION
# ============================================================

def get_db():
    conn = sqlite3.connect(
        DB_PATH,
        timeout=30
    )

    conn.row_factory = sqlite3.Row

    return conn


# ============================================================
# DATABASE INITIALIZATION
# ============================================================

def init_db():

    conn = get_db()
    cursor = conn.cursor()

    cursor.executescript("""

    -- ======================================================
    -- USERS
    -- ======================================================

    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,

        name TEXT NOT NULL,

        email TEXT UNIQUE NOT NULL,

        phone TEXT NOT NULL,

        role TEXT NOT NULL,

        avatar TEXT,

        nid_verified INTEGER DEFAULT 0,

        university TEXT,

        department TEXT,

        student_id TEXT,

        bio TEXT,

        password_hash TEXT,

        is_active INTEGER DEFAULT 1,

        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );


    -- ======================================================
    -- PROPERTY LISTINGS
    -- ======================================================

    CREATE TABLE IF NOT EXISTS listings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,

        owner_id INTEGER NOT NULL,

        title TEXT NOT NULL,

        description TEXT NOT NULL,

        property_type TEXT NOT NULL,

        address TEXT NOT NULL,

        area TEXT NOT NULL,

        university_nearby TEXT NOT NULL,

        distance_km REAL NOT NULL,

        rent_amount INTEGER NOT NULL,

        deposit_amount INTEGER NOT NULL,

        utilities_desc TEXT,

        gender_policy TEXT NOT NULL,

        availability_date TEXT NOT NULL,

        photos TEXT NOT NULL,

        lat REAL NOT NULL,

        lng REAL NOT NULL,

        facilities TEXT NOT NULL,

        is_verified INTEGER DEFAULT 0,

        is_flagged INTEGER DEFAULT 0,

        flag_reason TEXT,

        views_count INTEGER DEFAULT 0,

        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

        FOREIGN KEY (owner_id) REFERENCES users (id)
    );


    -- ======================================================
    -- ROOMMATE PROFILES
    -- ======================================================

    CREATE TABLE IF NOT EXISTS roommate_profiles (
        id INTEGER PRIMARY KEY AUTOINCREMENT,

        user_id INTEGER UNIQUE NOT NULL,

        budget_min INTEGER NOT NULL,

        budget_max INTEGER NOT NULL,

        preferred_area TEXT NOT NULL,

        preferred_university TEXT NOT NULL,

        sleep_schedule TEXT NOT NULL,

        study_habit TEXT NOT NULL,

        cleanliness TEXT NOT NULL,

        smoking TEXT NOT NULL,

        food_habit TEXT NOT NULL,

        guest_policy TEXT NOT NULL,

        hobbies TEXT,

        is_visible INTEGER DEFAULT 1,

        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

        FOREIGN KEY (user_id) REFERENCES users (id)
    );


    -- ======================================================
    -- ROOMMATE CONNECTIONS
    -- ======================================================

    CREATE TABLE IF NOT EXISTS roommate_connections (
        id INTEGER PRIMARY KEY AUTOINCREMENT,

        requester_id INTEGER NOT NULL,

        recipient_id INTEGER NOT NULL,

        status TEXT DEFAULT 'pending',

        message TEXT,

        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

        UNIQUE(requester_id, recipient_id)
    );


    -- ======================================================
    -- PROPERTY VISITS AND BOOKINGS
    -- ======================================================

    CREATE TABLE IF NOT EXISTS visits_and_bookings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,

        listing_id INTEGER NOT NULL,

        student_id INTEGER NOT NULL,

        owner_id INTEGER NOT NULL,

        visit_date TEXT NOT NULL,

        time_slot TEXT NOT NULL,

        status TEXT DEFAULT 'visit_requested',

        notes TEXT,

        simulated_deposit_paid INTEGER DEFAULT 0,

        deposit_amount INTEGER DEFAULT 0,

        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

        FOREIGN KEY (listing_id) REFERENCES listings (id),

        FOREIGN KEY (student_id) REFERENCES users (id),

        FOREIGN KEY (owner_id) REFERENCES users (id)
    );


    -- ======================================================
    -- REVIEWS
    -- ======================================================

    CREATE TABLE IF NOT EXISTS reviews (
        id INTEGER PRIMARY KEY AUTOINCREMENT,

        listing_id INTEGER NOT NULL,

        student_id INTEGER NOT NULL,

        rating INTEGER NOT NULL,

        cleanliness_rating INTEGER,

        owner_rating INTEGER,

        facilities_rating INTEGER,

        comment TEXT NOT NULL,

        is_verified_tenant INTEGER DEFAULT 1,

        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

        FOREIGN KEY (listing_id) REFERENCES listings (id),

        FOREIGN KEY (student_id) REFERENCES users (id)
    );


    -- ======================================================
    -- SCAM REPORTS
    -- ======================================================

    CREATE TABLE IF NOT EXISTS reports (
        id INTEGER PRIMARY KEY AUTOINCREMENT,

        listing_id INTEGER NOT NULL,

        reporter_id INTEGER NOT NULL,

        reason TEXT NOT NULL,

        details TEXT NOT NULL,

        status TEXT DEFAULT 'pending',

        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

        FOREIGN KEY (listing_id) REFERENCES listings (id),

        FOREIGN KEY (reporter_id) REFERENCES users (id)
    );


    -- ======================================================
    -- MAINTENANCE REQUESTS
    -- ======================================================

    CREATE TABLE IF NOT EXISTS maintenance_requests (
        id INTEGER PRIMARY KEY AUTOINCREMENT,

        listing_id INTEGER NOT NULL,

        tenant_id INTEGER NOT NULL,

        owner_id INTEGER NOT NULL,

        category TEXT NOT NULL,

        title TEXT NOT NULL,

        description TEXT NOT NULL,

        priority TEXT DEFAULT 'medium',

        status TEXT DEFAULT 'open',

        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

        resolved_at TIMESTAMP,

        FOREIGN KEY (listing_id) REFERENCES listings (id),

        FOREIGN KEY (tenant_id) REFERENCES users (id),

        FOREIGN KEY (owner_id) REFERENCES users (id)
    );


    -- ======================================================
    -- SAVED PROPERTY SEARCHES
    -- ======================================================

    CREATE TABLE IF NOT EXISTS saved_searches (
        id INTEGER PRIMARY KEY AUTOINCREMENT,

        user_id INTEGER NOT NULL,

        university TEXT,

        area TEXT,

        max_budget INTEGER,

        property_type TEXT,

        gender_policy TEXT,

        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

        FOREIGN KEY (user_id) REFERENCES users (id)
    );


    -- ======================================================
    -- MESS GROUPS
    -- ======================================================

    CREATE TABLE IF NOT EXISTS mess_groups (
        id INTEGER PRIMARY KEY AUTOINCREMENT,

        name TEXT NOT NULL,

        address TEXT NOT NULL,

        monthly_rent INTEGER NOT NULL,

        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );


    -- ======================================================
    -- MESS MEMBERS
    -- ======================================================

    CREATE TABLE IF NOT EXISTS mess_members (
        id INTEGER PRIMARY KEY AUTOINCREMENT,

        mess_id INTEGER NOT NULL,

        name TEXT NOT NULL,

        phone TEXT,

        seat_rent INTEGER NOT NULL,

        deposit INTEGER DEFAULT 0,

        FOREIGN KEY (mess_id) REFERENCES mess_groups (id)
    );


    -- ======================================================
    -- MESS MEALS
    -- ======================================================

    CREATE TABLE IF NOT EXISTS mess_meals (
        id INTEGER PRIMARY KEY AUTOINCREMENT,

        mess_id INTEGER NOT NULL,

        member_id INTEGER NOT NULL,

        meal_date TEXT NOT NULL,

        lunch_count REAL DEFAULT 1,

        dinner_count REAL DEFAULT 1,

        FOREIGN KEY (mess_id) REFERENCES mess_groups (id),

        FOREIGN KEY (member_id) REFERENCES mess_members (id)
    );


    -- ======================================================
    -- MESS BAZAAR
    -- ======================================================

    CREATE TABLE IF NOT EXISTS mess_bazaar (
        id INTEGER PRIMARY KEY AUTOINCREMENT,

        mess_id INTEGER NOT NULL,

        buyer_name TEXT NOT NULL,

        amount INTEGER NOT NULL,

        bazaar_date TEXT NOT NULL,

        items_description TEXT,

        FOREIGN KEY (mess_id) REFERENCES mess_groups (id)
    );


    -- ======================================================
    -- MESS UTILITIES
    -- ======================================================

    CREATE TABLE IF NOT EXISTS mess_utilities (
        id INTEGER PRIMARY KEY AUTOINCREMENT,

        mess_id INTEGER NOT NULL,

        title TEXT NOT NULL,

        amount INTEGER NOT NULL,

        month TEXT NOT NULL,

        paid_by TEXT,

        FOREIGN KEY (mess_id) REFERENCES mess_groups (id)
    );


    -- ======================================================
    -- NEW: AUTHENTICATION SESSIONS
    -- ======================================================

    CREATE TABLE IF NOT EXISTS auth_sessions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,

        user_id INTEGER NOT NULL,

        token_hash TEXT UNIQUE NOT NULL,

        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

        expires_at TEXT NOT NULL,

        FOREIGN KEY (user_id) REFERENCES users (id)
    );


    -- Index for faster session lookup

    CREATE INDEX IF NOT EXISTS idx_auth_sessions_token
    ON auth_sessions(token_hash);


    -- Index for session cleanup

    CREATE INDEX IF NOT EXISTS idx_auth_sessions_expiry
    ON auth_sessions(expires_at);


    """)

    conn.commit()


    # ========================================================
    # SAFE MIGRATION FOR EXISTING DATABASE
    # ========================================================
    #
    # CREATE TABLE IF NOT EXISTS does not add new columns
    # to an existing table.
    #
    # So we check existing columns before altering users.
    #
    # This preserves existing demo data.
    # ========================================================

    cursor.execute("PRAGMA table_info(users)")

    existing_columns = {
        row["name"]
        for row in cursor.fetchall()
    }


    # Add password hash column if missing.

    if "password_hash" not in existing_columns:

        cursor.execute("""
            ALTER TABLE users
            ADD COLUMN password_hash TEXT
        """)


    # Add account status column if missing.

    if "is_active" not in existing_columns:

        cursor.execute("""
            ALTER TABLE users
            ADD COLUMN is_active INTEGER DEFAULT 1
        """)


    # Production-safe, idempotent migrations: never drop the users' existing data.
    listing_columns = {r['name'] for r in conn.execute('PRAGMA table_info(listings)')}
    for column in ('owner_identity_checked','inspection_completed'):
        if column not in listing_columns:
            conn.execute(f'ALTER TABLE listings ADD COLUMN {column} INTEGER NOT NULL DEFAULT 0')
    for column in ('title_bn','description_bn'):
        if column not in listing_columns:
            conn.execute(f'ALTER TABLE listings ADD COLUMN {column} TEXT NOT NULL DEFAULT ""')

    conn.executescript("""
        CREATE TABLE IF NOT EXISTS search_alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            search_id INTEGER NOT NULL,
            listing_id INTEGER NOT NULL,
            seen_at TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id,search_id,listing_id)
        );
        CREATE INDEX IF NOT EXISTS idx_alert_user ON search_alerts(user_id, seen_at);
        CREATE TABLE IF NOT EXISTS property_comparisons (
            user_id INTEGER NOT NULL,
            listing_id INTEGER NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY(user_id,listing_id)
        );
        CREATE TABLE IF NOT EXISTS mess_memberships (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            mess_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL UNIQUE,
            member_name TEXT NOT NULL,
            seat_rent INTEGER NOT NULL DEFAULT 0,
            is_manager INTEGER NOT NULL DEFAULT 0,
            join_code TEXT UNIQUE,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
        CREATE INDEX IF NOT EXISTS idx_mess_memberships_group ON mess_memberships(mess_id);
        CREATE TABLE IF NOT EXISTS mess_expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            mess_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            kind TEXT NOT NULL CHECK(kind IN ('meal','bazaar','utility')),
            amount INTEGER NOT NULL CHECK(amount >= 0),
            entry_date TEXT NOT NULL,
            memo TEXT NOT NULL DEFAULT '',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
        CREATE INDEX IF NOT EXISTS idx_mess_expenses_month ON mess_expenses(mess_id,entry_date);
    """)
    # Expiring, one-use hashed password reset tokens (existing users preserved).
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS password_reset_tokens (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            token_hash TEXT NOT NULL UNIQUE,
            expires_at TEXT NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY(user_id) REFERENCES users(id)
        );
        CREATE INDEX IF NOT EXISTS idx_password_reset_expiry
            ON password_reset_tokens(expires_at);
    """)

    # Existing pending reports were required to be hidden, including imported data.
    conn.execute("""UPDATE listings SET is_flagged=1, flag_reason='Pending scam report'
       WHERE id IN (SELECT listing_id FROM reports WHERE status='pending')
         AND COALESCE(flag_reason,'') NOT IN ('Removed by owner','Removed by admin')""")
    conn.commit()
    conn.close()


# ============================================================
# START DATABASE INITIALIZATION
# ============================================================

if __name__ == "__main__":

    init_db()

    print("Database initialized successfully!")
    print("Existing data preserved.")
    print("Authentication tables are ready.")
