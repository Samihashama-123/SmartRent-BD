
import hashlib
import hmac
import secrets
import sqlite3

from datetime import datetime, timedelta, timezone

from app.database import get_db


# ============================================================
# SMARTRENT BD — AUTHENTICATION SYSTEM
# ============================================================

# Password security settings
PASSWORD_ITERATIONS = 600_000
PASSWORD_SALT_BYTES = 16

# Session settings
SESSION_COOKIE_NAME = "smartrent_session"
SESSION_DURATION_DAYS = 7

# Users may register with these roles only.
# Admin accounts must be created separately.
PUBLIC_ROLES = {"student", "landlord"}


# ============================================================
# PASSWORD HASHING
# ============================================================

def hash_password(password: str) -> str:
    """
    Securely hash a password using PBKDF2-HMAC-SHA256.
    Each password receives a random salt.
    """

    if not isinstance(password, str):
        raise ValueError("Invalid password.")

    if not 8 <= len(password) <= 128:
        raise ValueError(
            "Password must contain 8 to 128 characters."
        )

    salt = secrets.token_bytes(PASSWORD_SALT_BYTES)

    password_hash = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        PASSWORD_ITERATIONS
    )

    return (
        f"pbkdf2_sha256"
        f"${PASSWORD_ITERATIONS}"
        f"${salt.hex()}"
        f"${password_hash.hex()}"
    )


def verify_password(
    password: str,
    stored_hash: str
) -> bool:
    """
    Check a password against its stored hash.
    """

    if not password or not stored_hash:
        return False

    try:
        algorithm, iterations, salt_hex, hash_hex = (
            stored_hash.split("$")
        )

        if algorithm != "pbkdf2_sha256":
            return False

        rounds = int(iterations)

        if rounds < 1 or rounds > 2_000_000:
            return False

        salt = bytes.fromhex(salt_hex)
        expected_hash = bytes.fromhex(hash_hex)

        calculated_hash = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt,
            rounds
        )

        return hmac.compare_digest(
            calculated_hash,
            expected_hash
        )

    except (ValueError, TypeError, AttributeError):
        return False


# ============================================================
# USER REGISTRATION
# ============================================================

def register_user(
    name: str,
    email: str,
    phone: str,
    password: str,
    role: str = "student",
    university: str = "",
    department: str = ""
):
    """
    Create a student or landlord account.
    Public registration cannot create an admin.
    """

    name = (name or "").strip()
    email = (email or "").strip().lower()
    phone = (phone or "").strip()
    role = (role or "").strip().lower()

    university = (university or "").strip()
    department = (department or "").strip()

    if len(name) < 2 or len(name) > 100:
        raise ValueError(
            "Name must contain 2 to 100 characters."
        )

    if (
        len(email) > 254
        or email.count("@") != 1
        or "." not in email.split("@")[-1]
        or any(character.isspace() for character in email)
    ):
        raise ValueError("Enter a valid email address.")

    if len(phone) < 7 or len(phone) > 20:
        raise ValueError("Enter a valid phone number.")

    if role not in PUBLIC_ROLES:
        raise ValueError(
            "Only student and landlord registration is allowed."
        )

    if len(university) > 150:
        raise ValueError("University name is too long.")

    if len(department) > 100:
        raise ValueError("Department name is too long.")

    password_hash = hash_password(password)

    conn = get_db()

    try:
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO users (
                name,
                email,
                phone,
                role,
                password_hash,
                is_active,
                university,
                department,
                nid_verified
            )
            VALUES (?, ?, ?, ?, ?, 1, ?, ?, 0)
            """,
            (
                name,
                email,
                phone,
                role,
                password_hash,
                university,
                department
            )
        )

        user_id = cursor.lastrowid

        conn.commit()

        cursor.execute(
            """
            SELECT
                id,
                name,
                email,
                phone,
                role,
                avatar,
                nid_verified,
                university,
                department,
                is_active
            FROM users
            WHERE id = ?
            """,
            (user_id,)
        )

        user = cursor.fetchone()

        return dict(user) if user else None

    except sqlite3.IntegrityError:
        conn.rollback()

        raise ValueError(
            "An account with this email already exists."
        )

    finally:
        conn.close()


# ============================================================
# USER LOGIN VERIFICATION
# ============================================================

def authenticate_user(
    email: str,
    password: str
):
    """
    Validate login credentials.
    Return the user if authentication succeeds.
    """

    email = (email or "").strip().lower()

    conn = get_db()

    try:
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT *
            FROM users
            WHERE LOWER(email) = ?
            LIMIT 1
            """,
            (email,)
        )

        row = cursor.fetchone()

        if not row:
            return None

        user = dict(row)

        if user.get("is_active") != 1:
            return None

        if not verify_password(
            password,
            user.get("password_hash")
        ):
            return None

        # Do not return the password hash.
        user.pop("password_hash", None)

        return user

    finally:
        conn.close()


# ============================================================
# CREATE LOGIN SESSION
# ============================================================

def create_session(user_id: int) -> str:
    """
    Generate a cryptographically random session token.
    Store only its SHA-256 hash in the database.
    Return the raw token for the browser cookie.
    """

    token = secrets.token_urlsafe(32)

    token_hash = hashlib.sha256(
        token.encode("utf-8")
    ).hexdigest()

    expires_at = (
        datetime.now(timezone.utc)
        + timedelta(days=SESSION_DURATION_DAYS)
    ).isoformat()

    conn = get_db()

    try:
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO auth_sessions (
                user_id,
                token_hash,
                expires_at
            )
            VALUES (?, ?, ?)
            """,
            (
                user_id,
                token_hash,
                expires_at
            )
        )

        conn.commit()

        return token

    finally:
        conn.close()


# ============================================================
# GET LOGGED-IN USER FROM SESSION
# ============================================================

def get_user_by_session(token: str):
    """
    Validate a session token.
    Return the logged-in user or None.
    """

    if not token or not isinstance(token, str):
        return None

    token_hash = hashlib.sha256(
        token.encode("utf-8")
    ).hexdigest()

    now = datetime.now(timezone.utc).isoformat()

    conn = get_db()

    try:
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT
                u.id,
                u.name,
                u.email,
                u.phone,
                u.role,
                u.avatar,
                u.nid_verified,
                u.university,
                u.department,
                u.student_id,
                u.bio,
                u.is_active
            FROM auth_sessions s
            JOIN users u ON u.id = s.user_id
            WHERE s.token_hash = ?
              AND s.expires_at > ?
              AND u.is_active = 1
              AND u.password_hash IS NOT NULL
            LIMIT 1
            """,
            (
                token_hash,
                now
            )
        )

        row = cursor.fetchone()

        return dict(row) if row else None

    finally:
        conn.close()


# ============================================================
# DELETE SESSION / LOGOUT
# ============================================================

def delete_session(token: str) -> None:
    """
    Invalidate a login session.
    """

    if not token or not isinstance(token, str):
        return

    token_hash = hashlib.sha256(
        token.encode("utf-8")
    ).hexdigest()

    conn = get_db()

    try:
        cursor = conn.cursor()

        cursor.execute(
            """
            DELETE FROM auth_sessions
            WHERE token_hash = ?
            """,
            (token_hash,)
        )

        conn.commit()

    finally:
        conn.close()


# ============================================================
# CLEAN UP EXPIRED SESSIONS
# ============================================================

def cleanup_expired_sessions() -> int:
    """
    Remove expired sessions from the database.
    """

    now = datetime.now(timezone.utc).isoformat()

    conn = get_db()

    try:
        cursor = conn.cursor()

        cursor.execute(
            """
            DELETE FROM auth_sessions
            WHERE expires_at <= ?
            """,
            (now,)
        )

        deleted_count = cursor.rowcount

        conn.commit()

        return deleted_count

    finally:
        conn.close()
