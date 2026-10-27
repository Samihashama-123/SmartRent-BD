"""Local-only admin account setup. Run from VS Code terminal: python setup_admin.py"""
from getpass import getpass
from app.auth import hash_password
from app.database import get_db, init_db


def main():
    print("\nSmartRent BD — local administrator setup")
    print("This action changes only your local SQLite database.\n")
    init_db()
    email = input("Admin email address: ").strip().lower()
    if not email or email.count("@") != 1:
        print("Invalid email.")
        return
    with get_db() as conn:
        existing = conn.execute("SELECT id,role FROM users WHERE email=?", (email,)).fetchone()
        if existing and existing['role'] != 'admin':
            print("That email belongs to a non-admin account. No changes made.")
            return
        if not existing:
            print("New administrator account will be created.")
        else:
            print("Existing administrator password will be updated.")
    password = getpass("New admin password (8–128 characters): ")
    confirmation = getpass("Confirm password: ")
    if password != confirmation:
        print("Passwords do not match. No changes made.")
        return
    if len(password) < 12:
        print("Use a password with at least 12 characters.")
        return
    hashed = hash_password(password)
    with get_db() as conn:
        if existing:
            conn.execute("UPDATE users SET password_hash=?, is_active=1 WHERE id=?", (hashed,existing['id']))
            conn.execute("DELETE FROM auth_sessions WHERE user_id=?", (existing['id'],))
        else:
            name = input("Admin display name: ").strip() or "SmartRent Administrator"
            conn.execute("""INSERT INTO users
                (name,email,phone,role,password_hash,is_active,nid_verified)
                VALUES (?,?,?,'admin',?,1,0)""", (name,email,"Not provided",hashed))
    print("Admin credentials saved locally. Sign in through /login.")

if __name__ == '__main__':
    main()
