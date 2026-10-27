
import json
import sqlite3
import os

from urllib.parse import urlsplit, quote
from datetime import datetime

from fastapi import FastAPI, Request, Form, Depends, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.database import get_db, init_db
from app.matching import calculate_compatibility
from app.estimator import estimate_fair_rent, analyze_rent_fairness
from app.i18n import DEFAULT_LANGUAGE, get_language, translate
from app.content_localization import listing_text, has_listing_translation, enum_text, match_reason, profile_bio, has_bio_translation
from app.location_search import search_terms

from app.auth_routes import router as auth_router
from app.auth import SESSION_COOKIE_NAME, get_user_by_session
from app.landlord_routes import router as landlord_router
from app.features import router as features_router, create_search_alerts
# ============================================================
# SMARTRENT BD — FASTAPI APPLICATION
# ============================================================

app = FastAPI(
    title="SmartRent BD - Student Housing & Roommate Matching Platform"
)
app.include_router(auth_router)
app.include_router(landlord_router)
app.include_router(features_router)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

templates = Jinja2Templates(
    directory=os.path.join(BASE_DIR, "templates")
)

static_dir = os.path.join(BASE_DIR, "static")

if os.path.exists(static_dir):
    app.mount(
        "/static",
        StaticFiles(directory=static_dir),
        name="static"
    )


# ============================================================
# CUSTOM JINJA2 FILTERS
# ============================================================

def from_json_filter(val):
    if not val:
        return []

    if isinstance(val, (list, dict)):
        return val

    try:
        return json.loads(val)
    except Exception:
        return []


templates.env.filters["from_json"] = from_json_filter


# ============================================================
# ENGLISH / BANGLA LANGUAGE SYSTEM
# ============================================================

def render(request: Request, name: str, context: dict = None):
    context = dict(context or {})

    # Read the user's saved language preference
    lang = get_language(
        request.cookies.get(
            "smartrent_lang",
            DEFAULT_LANGUAGE
        )
    )

    # Available inside Jinja2 templates
    context["lang"] = lang

    # Templates can use: {{ t("find_housing") }}
    context["t"] = lambda key: translate(lang, key)
    context["tr_listing"] = lambda listing, field: listing_text(listing, field, lang)
    context["has_translation"] = lambda listing, field: has_listing_translation(listing, field, lang)
    context["tr_enum"] = lambda value: enum_text(value, lang)
    context["tr_reason"] = lambda value: match_reason(value, lang)
    context["tr_bio"] = lambda value: profile_bio(value, lang)
    context["has_bio_translation"] = lambda value: has_bio_translation(value, lang)

    return templates.TemplateResponse(
        request=request,
        name=name,
        context=context
    )


@app.get("/set-language")
async def set_language(
    request: Request,
    lang: str = DEFAULT_LANGUAGE
):
    language = get_language(lang)

    referrer = request.headers.get("referer", "")
    parsed = urlsplit(referrer)

    # Only redirect to a page on the same application.
    if (
        parsed.scheme in ("http", "https")
        and parsed.netloc == request.url.netloc
    ):
        destination = parsed.path or "/"

        if parsed.query:
            destination += "?" + parsed.query
    else:
        destination = "/"

    response = RedirectResponse(
        url=destination,
        status_code=303
    )

    # Remember the chosen language for one year.
    response.set_cookie(
        key="smartrent_lang",
        value=language,
        max_age=60 * 60 * 24 * 365,
        httponly=True,
        secure=request.url.scheme == "https",
        samesite="lax"
    )

    return response


# ============================================================
# DEMO USER PERSONA HELPER
# ============================================================

# IMPORTANT:
# This is the project's existing demo-role system.
# It is NOT secure authentication or authorization.
# Real login and role-based permissions must be added later.


# ============================================================
# REAL SESSION-BASED CURRENT USER
# ============================================================

def get_current_user(request: Request):
    token = request.cookies.get(SESSION_COOKIE_NAME)

    user = get_user_by_session(token)

    if not user:
        raise HTTPException(
            status_code=401,
            detail="Please sign in to continue."
        )

    if not user.get("avatar"):
        user["avatar"] = (
            "https://ui-avatars.com/api/"
            "?background=059669&color=ffffff&name=User"
        )

    return user


def get_optional_user(request: Request):
    """Public browsing never invents a logged-in identity."""
    return get_user_by_session(request.cookies.get(SESSION_COOKIE_NAME))


# ============================================================
# PAGE ACCESS PROTECTION
# ============================================================

@app.middleware("http")
async def protect_pages(request: Request, call_next):

    path = request.url.path

    # Browse housing publicly; private actions and dashboards require a session.
    protected_pages = {
        "/roommates", "/mess-manager", "/maintenance", "/fair-rent",
        "/agreement", "/landlord", "/admin", "/profile", "/my-bookings",
        "/compare", "/living-cost"
    }
    is_protected_page = path in protected_pages

    is_api = path.startswith("/api/")

    if not is_protected_page and not is_api:
        return await call_next(request)

    token = request.cookies.get(SESSION_COOKIE_NAME)
    user = get_user_by_session(token)

    if not user:
        if is_api:
            return JSONResponse(
                {"detail": "Authentication required."},
                status_code=401
            )

        next_page = path + (('?' + request.url.query) if request.url.query else '')
        return RedirectResponse(
            "/login?next=" + quote(next_page, safe=''),
            status_code=303
        )

    # Page permissions match menus. Hiding a link is never authorization.
    page_roles = {
        '/roommates': {'student'}, '/mess-manager': {'student'},
        '/my-bookings': {'student'}, '/landlord': {'landlord'},
        '/admin': {'admin'}, '/maintenance': {'student','landlord'},
        '/fair-rent': {'student'}, '/agreement': {'student','landlord'},
        '/compare': {'student'}, '/living-cost': {'student'}
    }
    allowed = page_roles.get(path)
    if allowed is not None and user['role'] not in allowed:
        denial = render(request, 'access_denied.html', {
            'current_user': user,
            'active_nav': 'none',
            'required_roles': ', '.join(sorted(allowed))
        })
        denial.status_code = 403
        return denial

    return await call_next(request)



# ============================================================
# BLOCK OLD INSECURE LANDLORD API ENDPOINTS
# ============================================================

@app.middleware("http")
async def block_legacy_landlord_endpoints(
    request: Request,
    call_next
):
    old_paths = {
        "/api/create-listing",
        "/api/update-visit-status",
        "/api/update-maintenance-status",
        "/api/add-bazaar",
        "/api/add-meal"
    }

    if (
        request.method == "POST"
        and request.url.path in old_paths
    ):
        return JSONResponse(
            {
                "detail": (
                    "This endpoint has been replaced by "
                    "the authenticated landlord API."
                )
            },
            status_code=410
        )

    return await call_next(request)


# ============================================================
# DATABASE INITIALIZATION
# ============================================================

@app.on_event("startup")
def startup_event():
    init_db()


# ============================================================
# HTML PAGE ROUTES
# ============================================================

# -------------------- HOMEPAGE --------------------

@app.get("/", response_class=HTMLResponse)
async def home_page(
    request: Request,
    role: str = "student"
):
    current_user = get_optional_user(request)

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT * FROM listings
WHERE is_flagged = 0 AND is_verified = 1
        ORDER BY is_verified DESC, views_count DESC
        LIMIT 6
    """)

    listings = [
        dict(row) for row in cursor.fetchall()
    ]

    conn.close()

    return render(
        request,
        "index.html",
        {
            "current_user": current_user,
            "active_nav": "home",
            "listings": listings
        }
    )


# -------------------- PROPERTY LISTINGS --------------------

@app.get("/listings", response_class=HTMLResponse)
async def listings_page(
    request: Request,
    role: str = "student",
    university: str = None,
    area: str = None,
    property_type: str = None,
    gender_policy: str = None,
    max_budget: int = None,
    max_distance: float = None,
    facility_wifi: int = None,
    facility_generator: int = None,
    facility_meals: int = None,
    facility_bath: int = None
):
    current_user = get_optional_user(request)

    conn = get_db()
    cursor = conn.cursor()

    query = """
        SELECT * FROM listings
        WHERE is_flagged = 0 AND is_verified = 1
    """

    params = []

    if university:
        query += """
            AND (
                LOWER(university_nearby) LIKE ?
                OR LOWER(title) LIKE ?
            )
        """

        params.extend([
            f"%{university.lower()}%",
            f"%{university.lower()}%"
        ])

    if area:
        # Search in both Bengali and English for common city/area names.
        # The map's place lookup is separate; this only matches existing listings.
        terms = search_terms(area)
        clauses = []
        for term in terms:
            clauses.append("(LOWER(area) LIKE ? OR LOWER(address) LIKE ?)")
            params.extend([f"%{term}%", f"%{term}%"])
        if clauses:
            query += " AND (" + " OR ".join(clauses) + ")"

    if property_type:
        query += " AND property_type = ?"
        params.append(property_type)

    if gender_policy:
        query += """
            AND (
                gender_policy = ?
                OR gender_policy = 'Any'
            )
        """
        params.append(gender_policy)

    if max_budget:
        query += " AND rent_amount <= ?"
        params.append(max_budget)

    if max_distance:
        query += " AND distance_km <= ?"
        params.append(max_distance)

    if facility_wifi:
        query += " AND facilities LIKE '%wifi%'"

    if facility_generator:
        query += " AND facilities LIKE '%generator%'"

    if facility_meals:
        query += " AND facilities LIKE '%meals%'"

    if facility_bath:
        query += " AND facilities LIKE '%attached_bath%'"

    query += " ORDER BY is_verified DESC, id DESC"

    cursor.execute(query, params)

    listings = [
        dict(row) for row in cursor.fetchall()
    ]

    conn.close()

    req_params = {
        "university": university,
        "area": area,
        "property_type": property_type,
        "gender_policy": gender_policy,
        "max_budget": max_budget,
        "max_distance": max_distance,
        "facility_wifi": facility_wifi,
        "facility_generator": facility_generator,
        "facility_meals": facility_meals,
        "facility_bath": facility_bath
    }

    return render(
        request,
        "listings.html",
        {
            "current_user": current_user,
            "active_nav": "listings",
            "listings": listings,
            "req_params": req_params
        }
    )


# -------------------- PROPERTY DETAILS --------------------

@app.get(
    "/listings/{listing_id}",
    response_class=HTMLResponse
)
async def listing_detail_page(
    request: Request,
    listing_id: int,
    role: str = "student"
):
    current_user = get_optional_user(request)
    viewing_user_id = current_user['id'] if current_user else -1
    viewing_user_role = current_user['role'] if current_user else 'guest'

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute(
        """
        UPDATE listings
        SET views_count = views_count + 1
        WHERE id = ?
          AND (
            (is_verified = 1 AND is_flagged = 0)
            OR (
                owner_id = ?
                AND COALESCE(flag_reason, '') != 'Removed by owner'
            )
            OR (
                ? = 'admin'
                AND COALESCE(flag_reason, '') != 'Removed by owner'
            )
          )
        """,
        (
            listing_id,
            viewing_user_id,
            viewing_user_role
        )
    )

    conn.commit()

    cursor.execute(
        """
        SELECT * FROM listings
        WHERE id = ?
          AND (
            (is_verified = 1 AND is_flagged = 0)
            OR (
                owner_id = ?
                AND COALESCE(flag_reason, '') != 'Removed by owner'
            )
            OR (
                ? = 'admin'
                AND COALESCE(flag_reason, '') != 'Removed by owner'
            )
          )
        """,
        (
            listing_id,
            viewing_user_id,
            viewing_user_role
        )
    )

    listing = cursor.fetchone()

    if not listing:
        conn.close()
        raise HTTPException(
            status_code=404,
            detail="Listing not found"
        )

    listing_dict = dict(listing)

    cursor.execute(
        "SELECT * FROM users WHERE id = ?",
        (listing_dict["owner_id"],)
    )

    owner = dict(cursor.fetchone() or {})

    cursor.execute(
        """
        SELECT
            r.*,
            u.name AS student_name,
            u.university AS student_univ
        FROM reviews r
        JOIN users u ON r.student_id = u.id
        WHERE r.listing_id = ? AND r.is_verified_tenant = 1
          AND EXISTS(SELECT 1 FROM visits_and_bookings v
             WHERE v.listing_id=r.listing_id AND v.student_id=r.student_id
               AND v.status='booked')
        ORDER BY r.id DESC
        """,
        (listing_id,)
    )

    reviews = [
        dict(row) for row in cursor.fetchall()
    ]
    my_visits = []
    if current_user and current_user['role'] == 'student':
        my_visits = [dict(r) for r in cursor.execute("""SELECT * FROM visits_and_bookings
          WHERE listing_id=? AND student_id=? ORDER BY id DESC""",
            (listing_id,viewing_user_id)).fetchall()]
    confirmed_tenant = any(v['status']=='booked' for v in my_visits)
    scheduled_visit = next((v for v in my_visits if v['status']=='visit_scheduled'),None)
    pending_booking = next((v for v in my_visits if v['status']=='booking_requested'),None)

    facs = from_json_filter(
        listing_dict.get("facilities", "[]")
    )

    est = estimate_fair_rent(
        area=listing_dict.get("area", ""),
        property_type=listing_dict.get(
            "property_type",
            "Mess Seat"
        ),
        distance_km=listing_dict.get(
            "distance_km",
            1.0
        ),
        facilities=facs
    )

    fair_analysis = analyze_rent_fairness(
        listing_dict.get("rent_amount", 4000),
        est["recommended_rent"]
    )

    conn.close()

    return render(
        request,
        "listing_detail.html",
        {
            "current_user": current_user,
            "active_nav": "listings",
            "listing": listing_dict,
            "owner": owner,
            "reviews": reviews,
            "my_visits": my_visits,
            "confirmed_tenant": confirmed_tenant,
            "scheduled_visit": scheduled_visit,
            "pending_booking": pending_booking,
            "fair_analysis": fair_analysis
        }
    )


# -------------------- ROOMMATE MATCHING --------------------

@app.get("/roommates", response_class=HTMLResponse)
async def roommates_page(
    request: Request,
    role: str = "student",
    university: str = None,
    sleep: str = None,
    smoking: str = None,
    cleanliness: str = None
):
    current_user = get_current_user(request)
    if current_user["role"] != "student":
        raise HTTPException(status_code=403, detail="Student account required.")
    with get_db() as conn:
        my_row=conn.execute("SELECT * FROM roommate_profiles WHERE user_id=?",
            (current_user["id"],)).fetchone()
        my_profile=dict(my_row) if my_row else {
            "user_id":current_user["id"],"budget_min":3500,"budget_max":6500,
            "preferred_area":"Any area","preferred_university":current_user.get("university") or "",
            "sleep_schedule":"flexible","study_habit":"silent","cleanliness":"moderate",
            "smoking":"non_smoker","food_habit":"flexible","guest_policy":"daytime_only",
            "is_visible":0
        }
        query="""SELECT rp.*, u.name,u.university,u.department,u.phone,u.avatar,u.nid_verified
            FROM roommate_profiles rp JOIN users u ON rp.user_id=u.id
            WHERE rp.user_id!=? AND rp.is_visible=1 AND u.role='student' AND u.is_active=1"""
        params=[current_user["id"]]
        if university:
            query+=" AND LOWER(u.university) LIKE ?";params.append('%'+university.lower()[:100]+'%')
        for name,value in (("sleep_schedule",sleep),("smoking",smoking),("cleanliness",cleanliness)):
            if value:
                query+=f" AND rp.{name}=?";params.append(value)
        candidates=[dict(r) for r in conn.execute(query,params).fetchall()]
        connection_rows=conn.execute("""SELECT * FROM roommate_connections
            WHERE requester_id=? OR recipient_id=?""",
            (current_user["id"],current_user["id"])).fetchall()
        connections={
            (r['recipient_id'] if r['requester_id']==current_user['id'] else r['requester_id']):r['status']
            for r in connection_rows
        }
        incoming_requests=[dict(r) for r in conn.execute("""SELECT rc.id,rc.requester_id,u.name,u.university
            FROM roommate_connections rc JOIN users u ON u.id=rc.requester_id
            WHERE rc.recipient_id=? AND rc.status='pending' ORDER BY rc.id DESC""",
            (current_user["id"],)).fetchall()]
    matches=[]
    for candidate in candidates:
        compat=calculate_compatibility(my_profile,candidate)
        status=connections.get(candidate['user_id'],'none')
        matches.append({"profile":candidate,"compatibility":compat,
                        "connection_status":status,"is_connected":status=='accepted'})
    matches.sort(key=lambda x:x['compatibility']['score'],reverse=True)
    return render(request,"roommates.html",{
        "current_user":current_user,"active_nav":"roommates","candidate_matches":matches,
        "my_profile":my_profile,"incoming_requests":incoming_requests,"not_student":False,
        "req_params":{"university":university,"sleep":sleep,"smoking":smoking,"cleanliness":cleanliness}
    })


# -------------------- MESS MANAGER --------------------

@app.get("/mess-manager", response_class=HTMLResponse)
async def mess_manager_page(request: Request):
    from app.features import mess_workspace_page
    return await mess_workspace_page(request)


# -------------------- MAINTENANCE --------------------

def get_maintenance_listing_options(user):
    if user['role'] != 'student':
        return []
    with get_db() as conn:
        return conn.execute("""SELECT l.id,l.title FROM listings l
            WHERE l.is_verified=1 AND l.is_flagged=0 AND EXISTS
            (SELECT 1 FROM visits_and_bookings v WHERE v.listing_id=l.id
             AND v.student_id=? AND v.status='booked')
            ORDER BY l.id DESC LIMIT 100""",(user['id'],)).fetchall()


@app.get("/maintenance", response_class=HTMLResponse)
async def maintenance_page(request: Request, role: str = "student"):
    user=get_current_user(request)
    with get_db() as conn:
        if user['role']=='admin':
            tickets=[dict(r) for r in conn.execute("""SELECT m.*,u.name AS tenant_name,
                o.name AS owner_name,l.title AS listing_title
                FROM maintenance_requests m JOIN users u ON m.tenant_id=u.id
                JOIN users o ON m.owner_id=o.id JOIN listings l ON m.listing_id=l.id
                ORDER BY m.id DESC""").fetchall()]
        else:
            field='owner_id' if user['role']=='landlord' else 'tenant_id'
            tickets=[dict(r) for r in conn.execute(f"""SELECT m.*,u.name AS tenant_name,
                o.name AS owner_name,l.title AS listing_title
                FROM maintenance_requests m JOIN users u ON m.tenant_id=u.id
                JOIN users o ON m.owner_id=o.id JOIN listings l ON m.listing_id=l.id
                WHERE m.{field}=? ORDER BY m.id DESC""",(user['id'],)).fetchall()]
    return render(request,"maintenance.html",{
        "current_user":user,"active_nav":"maintenance",
        "open_tickets":[t for t in tickets if t['status']=='open'],
        "in_progress_tickets":[t for t in tickets if t['status']=='in_progress'],
        "resolved_tickets":[t for t in tickets if t['status']=='resolved'],
        "available_listings":[dict(r) for r in get_maintenance_listing_options(user)]
    })


# -------------------- FAIR RENT CALCULATOR --------------------

@app.get("/fair-rent", response_class=HTMLResponse)
async def fair_rent_page(
    request: Request,
    role: str = "student"
):
    current_user = get_current_user(request)

    return render(
        request,
        "fair_rent.html",
        {
            "current_user": current_user,
            "active_nav": "fair_rent"
        }
    )


# -------------------- RENTAL AGREEMENT --------------------

@app.get("/agreement", response_class=HTMLResponse)
async def agreement_page(
    request: Request,
    listing_id: int = 1,
    role: str = "student"
):
    current_user = get_current_user(request)

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute(
        """SELECT * FROM listings
        WHERE id = ? AND (
            (is_verified = 1 AND is_flagged = 0)
            OR (
                owner_id = ?
                AND COALESCE(flag_reason, '') != 'Removed by owner'
            )
            OR (
                ? = 'admin'
                AND COALESCE(flag_reason, '') != 'Removed by owner'
            )
        )""",
        (
            listing_id,
            current_user["id"],
            current_user["role"]
        )
    )

    listing = cursor.fetchone()

    listing_dict = (
        dict(listing)
        if listing
        else None
    )

    owner = None

    if listing_dict:
        cursor.execute(
            "SELECT * FROM users WHERE id = ?",
            (listing_dict["owner_id"],)
        )

        owner = dict(
            cursor.fetchone() or {}
        )

    conn.close()

    return render(
        request,
        "agreement.html",
        {
            "current_user": current_user,
            "active_nav": "agreement",
            "listing": listing_dict,
            "owner": owner
        }
    )


# -------------------- MY VISITS & BOOKINGS --------------------

@app.get("/my-bookings", response_class=HTMLResponse)
async def my_bookings_page(request: Request):
    current_user = get_current_user(request)
    if current_user["role"] != "student":
        return RedirectResponse("/profile", status_code=303)
    with get_db() as conn:
        rows = conn.execute("""
            SELECT v.id, v.listing_id, v.visit_date, v.time_slot, v.status,
                   v.created_at, l.title AS listing_title, l.area,
                   l.rent_amount, u.name AS owner_name
            FROM visits_and_bookings v
            JOIN listings l ON l.id = v.listing_id
            JOIN users u ON u.id = v.owner_id
            WHERE v.student_id = ?
            ORDER BY v.id DESC
        """, (current_user["id"],)).fetchall()
    return render(request, "my_bookings.html", {
        "current_user": current_user,
        "active_nav": "my_bookings",
        "bookings": [dict(r) for r in rows]
    })


# -------------------- LANDLORD DASHBOARD --------------------

@app.get("/landlord", response_class=HTMLResponse)
async def landlord_portal(
    request: Request,
    role: str = "landlord"
):
    current_user = get_current_user(request)

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT * FROM listings
        WHERE owner_id = ?
        ORDER BY id DESC
        """,
        (current_user["id"],)
    )

    my_listings = [
        dict(row) for row in cursor.fetchall()
    ]

    cursor.execute(
        """
        SELECT
            vb.*,
            u.name AS student_name,
            u.university AS student_university,
            l.title AS listing_title
        FROM visits_and_bookings vb
        JOIN users u ON vb.student_id = u.id
        JOIN listings l ON vb.listing_id = l.id
        WHERE vb.owner_id = ?
        ORDER BY vb.id DESC
        """,
        (current_user["id"],)
    )

    visits = [
        dict(row) for row in cursor.fetchall()
    ]

    cursor.execute(
        """
        SELECT
            mr.*,
            u.name AS tenant_name,
            l.title AS listing_title
        FROM maintenance_requests mr
        JOIN users u ON mr.tenant_id = u.id
        JOIN listings l ON mr.listing_id = l.id
        WHERE mr.owner_id = ?
        ORDER BY mr.id DESC
        """,
        (current_user["id"],)
    )

    maintenance_items = [
        dict(row) for row in cursor.fetchall()
    ]

    conn.close()

    return render(
        request,
        "landlord.html",
        {
            "current_user": current_user,
            "active_nav": "landlord",
            "my_listings": my_listings,
            "visits": visits,
            "maintenance_items": maintenance_items
        }
    )


# -------------------- ADMIN DASHBOARD --------------------

@app.get("/admin", response_class=HTMLResponse)
async def admin_portal(
    request: Request,
    role: str = "admin"
):
    current_user = get_current_user(request)

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT
            rep.*,
            l.title AS listing_title,
            u.name AS reporter_name,
            u.university AS reporter_university
        FROM reports rep
        JOIN listings l ON rep.listing_id = l.id
        JOIN users u ON rep.reporter_id = u.id
        WHERE rep.status = 'pending'
        ORDER BY rep.id DESC
        """
    )

    reports = [
        dict(row) for row in cursor.fetchall()
    ]

    cursor.execute(
        """
        SELECT
            l.*,
            u.name AS owner_name,
            u.phone AS owner_phone
        
FROM listings l
JOIN users u ON l.owner_id = u.id
WHERE l.is_flagged = 0
ORDER BY l.is_verified ASC, l.id DESC

        """
    )

    all_listings = [
        dict(row) for row in cursor.fetchall()
    ]

    cursor.execute(
        """
        SELECT COUNT(*)
        FROM listings
        WHERE is_verified = 1
        """
    )

    verified_count = cursor.fetchone()[0]

    cursor.execute(
        "SELECT COUNT(*) FROM users"
    )

    total_users = cursor.fetchone()[0]

    conn.close()

    return render(
        request,
        "admin.html",
        {
            "current_user": current_user,
            "active_nav": "admin",
            "reports": reports,
            "all_listings": all_listings,
            "verified_count": verified_count,
            "total_users": total_users
        }
    )


# -------------------- USER PROFILE --------------------

@app.get("/profile", response_class=HTMLResponse)
async def profile_page(
    request: Request,
    role: str = "student"
):
    current_user = get_current_user(request)

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT * FROM saved_searches
        WHERE user_id = ?
        ORDER BY id DESC
        """,
        (current_user["id"],)
    )

    saved_searches = [
        dict(row) for row in cursor.fetchall()
    ]

    alerts = [dict(r) for r in cursor.execute("""SELECT a.*,l.title,l.area,l.rent_amount
        FROM search_alerts a JOIN listings l ON l.id=a.listing_id
        WHERE a.user_id=? AND l.is_verified=1 AND l.is_flagged=0
        ORDER BY a.id DESC LIMIT 40""",(current_user['id'],)).fetchall()]
    conn.close()

    return render(
        request,
        "profile.html",
        {
            "current_user": current_user,
            "active_nav": "profile",
            "saved_searches": saved_searches,
            "search_alerts": alerts
        }
    )



# ============================================================
# AUTHORIZATION & INPUT VALIDATION
# ============================================================

def require_action(request: Request, roles=("student", "landlord", "admin")):
    user = get_current_user(request)
    if user["role"] not in roles:
        raise HTTPException(403, "Not permitted for this account role.")
    source = request.headers.get("origin") or request.headers.get("referer")
    if not source:
        raise HTTPException(403, "Missing request origin.")
    source_url = urlsplit(source)
    if (source_url.scheme, source_url.netloc) != (request.url.scheme, request.url.netloc):
        raise HTTPException(403, "Cross-origin request blocked.")
    return user

def limited_text(value, label, lower=1, upper=1000):
    value = (value or "").strip()
    if not lower <= len(value) <= upper:
        raise HTTPException(422, f"{label} must be {lower}-{upper} characters.")
    return value

def public_listing(conn, listing_id):
    row = conn.execute("""SELECT id, owner_id FROM listings
        WHERE id=? AND is_verified=1 AND is_flagged=0""", (listing_id,)).fetchone()
    if not row:
        raise HTTPException(404, "This listing is not available.")
    return row

# ============================================================
# JSON / FORM API ENDPOINTS
# ============================================================

# -------------------- REQUEST PROPERTY VISIT --------------------

@app.post("/api/request-visit")
async def api_request_visit(
    request: Request,
    listing_id: int = Form(...),
    student_id: int = Form(...),
    owner_id: int = Form(...),
    visit_date: str = Form(...),
    time_slot: str = Form(...),
    notes: str = Form("")
):
    from datetime import date
    user = require_action(request, ("student",))
    try:
        day = date.fromisoformat(visit_date)
    except ValueError:
        raise HTTPException(422, "Select a valid visit date.")
    if day < date.today():
        raise HTTPException(422, "Visit date cannot be in the past.")
    slot = limited_text(time_slot, "Time slot", 2, 80)
    memo = limited_text(notes, "Notes", 0, 500)
    with get_db() as conn:
        listing = public_listing(conn, listing_id)
        if listing["owner_id"] == user["id"]:
            raise HTTPException(403, "Cannot request your own property.")
        conn.execute("""INSERT INTO visits_and_bookings
            (listing_id,student_id,owner_id,visit_date,time_slot,notes,status)
            VALUES (?,?,?,?,?,?,'visit_requested')""",
            (listing_id,user["id"],listing["owner_id"],day.isoformat(),slot,memo))
    return {"status":"success", "message":"Visit request sent to landlord."}


# -------------------- SIMULATED BOOKING --------------------

@app.post("/api/simulated-booking")
async def api_simulated_booking(
    request: Request,
    listing_id: int = Form(...),
    student_id: int = Form(0),
    owner_id: int = Form(0),
    deposit_amount: int = Form(0),
    visit_id: int = Form(0)
):
    user = require_action(request, ("student",))
    with get_db() as conn:
        public_listing(conn, listing_id)
        if visit_id:
            visit = conn.execute("""SELECT id FROM visits_and_bookings
              WHERE id=? AND student_id=? AND listing_id=? AND status='visit_scheduled'""",
              (visit_id,user['id'],listing_id)).fetchone()
        else:
            visit = conn.execute("""SELECT id FROM visits_and_bookings
              WHERE student_id=? AND listing_id=? AND status='visit_scheduled'
              ORDER BY id DESC LIMIT 1""",(user['id'],listing_id)).fetchone()
        if not visit:
            raise HTTPException(409,"Landlord must schedule your visit before you can request booking.")
        conn.execute("""UPDATE visits_and_bookings SET status='booking_requested',
          simulated_deposit_paid=0,deposit_amount=0 WHERE id=?""",(visit['id'],))
    return {"status":"success", "message":"Booking request sent. The landlord must confirm it. No payment was processed."}


# -------------------- REPORT A LISTING --------------------

@app.post("/api/report-listing")
async def api_report_listing(
    request: Request,
    listing_id: int = Form(...),
    reporter_id: int = Form(...),
    reason: str = Form(...),
    details: str = Form(...)
):
    user = require_action(request)
    reason = limited_text(reason, "Reason", 3, 100)
    details = limited_text(details, "Details", 5, 2000)
    with get_db() as conn:
        public_listing(conn, listing_id)
        existing = conn.execute("""SELECT id FROM reports WHERE
            listing_id=? AND reporter_id=? AND status='pending'""",
            (listing_id,user["id"])).fetchone()
        if existing:
            raise HTTPException(409, "You already have a pending report for this listing.")
        conn.execute("""INSERT INTO reports (listing_id,reporter_id,reason,details,status)
            VALUES (?,?,?,?,'pending')""", (listing_id,user["id"],reason,details))
        conn.execute("""UPDATE listings SET is_flagged=1,flag_reason='Pending scam report'
            WHERE id=? AND COALESCE(flag_reason,'') NOT IN
            ('Removed by owner','Removed by admin')""", (listing_id,))
    return {"status":"success", "message":"Listing hidden while the admin reviews your report."}


# -------------------- SUBMIT TENANT REVIEW --------------------

@app.post("/api/submit-review")
async def api_submit_review(
    request: Request,
    listing_id: int = Form(...),
    student_id: int = Form(...),
    rating: int = Form(...),
    cleanliness_rating: int = Form(5),
    owner_rating: int = Form(5),
    facilities_rating: int = Form(5),
    comment: str = Form(...)
):
    user = require_action(request, ("student",))
    if not all(1 <= v <= 5 for v in (rating, cleanliness_rating, owner_rating, facilities_rating)):
        raise HTTPException(422, "Ratings must be between 1 and 5.")
    comment = limited_text(comment,"Review",5,1000)
    with get_db() as conn:
        listing = public_listing(conn, listing_id)
        if listing["owner_id"] == user["id"]:
            raise HTTPException(403,"Cannot review your own property.")
        verified = conn.execute("""SELECT id FROM visits_and_bookings
            WHERE listing_id=? AND student_id=? AND status='booked' LIMIT 1""",
            (listing_id,user['id'])).fetchone()
        if not verified:
            raise HTTPException(403, "Only tenants with a confirmed booking can review this listing.")
        previous = conn.execute("""SELECT id FROM reviews
            WHERE listing_id=? AND student_id=?""",(listing_id,user['id'])).fetchone()
        if previous:
            raise HTTPException(409,"You already reviewed this property.")
        conn.execute("""INSERT INTO reviews
            (listing_id,student_id,rating,cleanliness_rating,owner_rating,
             facilities_rating,comment,is_verified_tenant)
            VALUES (?,?,?,?,?,?,?,1)""",
            (listing_id,user["id"],rating,cleanliness_rating,owner_rating,facilities_rating,comment))
    return {"status":"success", "message":"Verified tenant review published."}


# -------------------- ROOMMATE CONNECTION --------------------

@app.post("/api/request-connect")
async def api_request_connect(
    request: Request,
    requester_id: int = Form(...),
    recipient_id: int = Form(...)
):
    user = require_action(request, ("student",))
    if recipient_id == user["id"]:
        raise HTTPException(422, "Cannot connect to yourself.")
    with get_db() as conn:
        target = conn.execute("""SELECT rp.user_id FROM roommate_profiles rp
           JOIN users u ON u.id=rp.user_id
           WHERE rp.user_id=? AND rp.is_visible=1 AND u.role='student'
             AND u.is_active=1""", (recipient_id,)).fetchone()
        if not target:
            raise HTTPException(404, "Roommate profile unavailable.")
        existing = conn.execute("""SELECT id,status FROM roommate_connections
            WHERE (requester_id=? AND recipient_id=?)
               OR (requester_id=? AND recipient_id=?)""",
            (user["id"], recipient_id, recipient_id, user["id"])).fetchone()
        if existing:
            raise HTTPException(409, "Connection request already exists. Check your requests.")
        conn.execute("""INSERT INTO roommate_connections
            (requester_id,recipient_id,status) VALUES (?,?,'pending')""",
            (user["id"], recipient_id))
    return {"status":"success", "message":"Request sent. Contact unlocks only after acceptance."}


# -------------------- UPDATE ROOMMATE PROFILE --------------------

@app.post("/api/update-roommate-profile")
async def api_update_roommate_profile(
    request: Request,
    user_id: int = Form(...),
    budget_min: int = Form(...),
    budget_max: int = Form(...),
    preferred_area: str = Form(...),
    sleep_schedule: str = Form(...),
    study_habit: str = Form(...),
    cleanliness: str = Form(...),
    smoking: str = Form(...),
    guest_policy: str = Form(...),
    hobbies: str = Form("")
):
    user = require_action(request, ("student",))
    if not (0 <= budget_min <= budget_max <= 500_000):
        raise HTTPException(422, "Invalid budget range.")
    area = limited_text(preferred_area,"Preferred area",2,100)
    hobbies = limited_text(hobbies,"Bio",0,500)
    with get_db() as conn:
        current = conn.execute("SELECT * FROM roommate_profiles WHERE user_id=?",
            (user["id"],)).fetchone()
        if current:
            conn.execute("""UPDATE roommate_profiles SET budget_min=?,budget_max=?,
                preferred_area=?,sleep_schedule=?,study_habit=?,cleanliness=?,smoking=?,
                guest_policy=?,hobbies=? WHERE user_id=?""",
                (budget_min,budget_max,area,sleep_schedule,study_habit,cleanliness,
                 smoking,guest_policy,hobbies,user["id"]))
        else:
            conn.execute("""INSERT INTO roommate_profiles
                (user_id,budget_min,budget_max,preferred_area,preferred_university,
                sleep_schedule,study_habit,cleanliness,smoking,food_habit,
                guest_policy,hobbies,is_visible) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,1)""",
                (user["id"],budget_min,budget_max,area,user.get("university") or "",
                 sleep_schedule,study_habit,cleanliness,smoking,"flexible",guest_policy,hobbies))
    return {"status":"success", "message":"Roommate preferences saved."}




@app.post("/api/roommate-respond")
async def api_roommate_respond(
    request: Request,
    connection_id: int = Form(...),
    decision: str = Form(...)
):
    user = require_action(request, ("student",))
    if decision not in {"accept", "decline"}:
        raise HTTPException(422,"Invalid decision.")
    with get_db() as conn:
        row=conn.execute("""SELECT id FROM roommate_connections
            WHERE id=? AND recipient_id=? AND status='pending'""",
            (connection_id,user['id'])).fetchone()
        if not row:
            raise HTTPException(404,"Pending request not found.")
        conn.execute("UPDATE roommate_connections SET status=? WHERE id=?",
            ('accepted' if decision=='accept' else 'declined',connection_id))
    return {"status":"success","message":"Connection preference saved."}

@app.post("/api/roommate-visibility")
async def api_roommate_visibility(request: Request, visible: int = Form(...)):
    user=require_action(request,("student",))
    if visible not in (0,1):
        raise HTTPException(422,"Invalid visibility setting.")
    with get_db() as conn:
        row=conn.execute("UPDATE roommate_profiles SET is_visible=? WHERE user_id=?",
            (visible,user['id']))
        if row.rowcount==0:
            raise HTTPException(404,"Create your roommate profile first.")
    return {"status":"success","message":"Profile visibility updated."}

# -------------------- SAVE PROPERTY SEARCH --------------------

@app.post("/api/save-search")
async def api_save_search(
    request: Request,
    user_id: int = Form(...),
    university: str = Form(""),
    area: str = Form(""),
    max_budget: int = Form(6000)
):
    user = require_action(request, ("student", "landlord"))
    if not 0 <= max_budget <= 1_000_000:
        raise HTTPException(422,"Budget is out of range.")
    with get_db() as conn:
        conn.execute("""INSERT INTO saved_searches (user_id,university,area,max_budget)
            VALUES (?,?,?,?)""",(user["id"],university[:150],area[:100],max_budget))
    return {"status":"success", "message":"Search saved. New approved matching listings will appear as in-app alerts."}


# -------------------- ADD BAZAAR EXPENSE --------------------

@app.post("/api/add-bazaar")
async def api_add_bazaar(
    request: Request,
    mess_id: int = Form(1),
    buyer_name: str = Form(...),
    amount: int = Form(...),
    items_description: str = Form("")
):
    require_action(request, ("student",))
    if not 1 <= amount <= 1_000_000:
        raise HTTPException(422,"Enter a valid expense amount.")
    buyer_name = limited_text(buyer_name,"Buyer",2,100)
    memo = limited_text(items_description,"Items",0,500)
    with get_db() as conn:
        member = conn.execute("""SELECT id FROM mess_members WHERE
            mess_id=? AND name=?""",(mess_id,buyer_name)).fetchone()
        if not member:
            raise HTTPException(422,"Choose a member in this demo mess.")
        conn.execute("""INSERT INTO mess_bazaar
            (mess_id,buyer_name,amount,bazaar_date,items_description)
            VALUES (?,?,?,date('now'),?)""",(mess_id,buyer_name,amount,memo))
    return {"status":"success", "message":"Demo mess expense recorded."}


# -------------------- ADD DAILY MEAL --------------------

@app.post("/api/add-meal")
async def api_add_meal(
    request: Request,
    mess_id: int = Form(1),
    member_id: int = Form(...),
    meal_date: str = Form(...),
    lunch_count: float = Form(1.0),
    dinner_count: float = Form(1.0)
):
    from datetime import date
    require_action(request,("student",))
    try:
        date.fromisoformat(meal_date)
    except ValueError:
        raise HTTPException(422,"Invalid meal date.")
    if not all(0 <= n <= 5 for n in (lunch_count,dinner_count)):
        raise HTTPException(422,"Meal count must be 0 to 5.")
    with get_db() as conn:
        member = conn.execute("SELECT id FROM mess_members WHERE id=? AND mess_id=?",
            (member_id,mess_id)).fetchone()
        if not member:
            raise HTTPException(422,"Member is not in this demo mess.")
        conn.execute("""INSERT INTO mess_meals
            (mess_id,member_id,meal_date,lunch_count,dinner_count)
            VALUES (?,?,?,?,?)""",(mess_id,member_id,meal_date,lunch_count,dinner_count))
    return {"status":"success", "message":"Demo meal recorded."}


# -------------------- SUBMIT MAINTENANCE --------------------

@app.post("/api/submit-maintenance")
async def api_submit_maintenance(
    request: Request,
    tenant_id: int = Form(...),
    listing_id: int = Form(...),
    owner_id: int = Form(...),
    category: str = Form(...),
    title: str = Form(...),
    description: str = Form(...),
    priority: str = Form("medium")
):
    user = require_action(request,("student",))
    category=limited_text(category,"Category",2,80)
    title=limited_text(title,"Title",5,150)
    description=limited_text(description,"Description",10,1500)
    if priority not in {"low","medium","high","urgent"}:
        raise HTTPException(422,"Invalid priority.")
    with get_db() as conn:
        listing=public_listing(conn,listing_id)
        if listing["owner_id"]==user["id"]:
            raise HTTPException(403,"Not permitted.")
        tenant = conn.execute("""SELECT id FROM visits_and_bookings
            WHERE listing_id=? AND student_id=? AND status='booked' LIMIT 1""",
            (listing_id,user['id'])).fetchone()
        if not tenant:
            raise HTTPException(403,'Only confirmed tenants can submit maintenance for a property.')
        conn.execute("""INSERT INTO maintenance_requests
            (listing_id,tenant_id,owner_id,category,title,description,priority,status)
            VALUES (?,?,?,?,?,?,?,'open')""",
            (listing_id,user["id"],listing["owner_id"],category,title,description,priority))
    return {"status":"success", "message":"Maintenance request sent."}


# -------------------- UPDATE MAINTENANCE STATUS --------------------

@app.post("/api/update-maintenance-status")
async def api_update_maintenance_status(
    ticket_id: int = Form(...),
    status: str = Form(...)
):
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute(
        """
        UPDATE maintenance_requests
        SET status = ?
        WHERE id = ?
        """,
        (
            status,
            ticket_id
        )
    )

    conn.commit()
    conn.close()

    return JSONResponse({
        "status": "success",
        "message": "Status updated."
    })


# -------------------- UPDATE VISIT STATUS --------------------

@app.post("/api/update-visit-status")
async def api_update_visit_status(
    visit_id: int = Form(...),
    status: str = Form(...)
):
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute(
        """
        UPDATE visits_and_bookings
        SET status = ?
        WHERE id = ?
        """,
        (
            status,
            visit_id
        )
    )

    conn.commit()
    conn.close()

    return JSONResponse({
        "status": "success",
        "message": "Visit status updated."
    })


# -------------------- CREATE PROPERTY LISTING --------------------

@app.post("/api/create-listing")
async def api_create_listing(
    owner_id: int = Form(...),
    title: str = Form(...),
    property_type: str = Form(...),
    rent_amount: int = Form(...),
    deposit_amount: int = Form(...),
    area: str = Form(...),
    university_nearby: str = Form(...),
    address: str = Form(...),
    description: str = Form(...),
    gender_policy: str = Form("Male Only"),
    fac_wifi: str = Form(None),
    fac_gen: str = Form(None),
    fac_water: str = Form(None),
    fac_meals: str = Form(None),
    fac_bath: str = Form(None),
    fac_lift: str = Form(None)
):
    facs = []

    if fac_wifi:
        facs.append("wifi")

    if fac_gen:
        facs.append("generator")

    if fac_water:
        facs.append("water_247")

    if fac_meals:
        facs.append("meals")

    if fac_bath:
        facs.append("attached_bath")

    if fac_lift:
        facs.append("lift")

    sample_photos = json.dumps([
        (
            "https://images.unsplash.com/"
            "photo-1555854877-bab0e564b8d5"
            "?w=800&auto=format&fit=crop&q=80"
        ),
        (
            "https://images.unsplash.com/"
            "photo-1595526114035-0d45ed16cfbf"
            "?w=800&auto=format&fit=crop&q=80"
        )
    ])

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO listings (
            owner_id,
            title,
            description,
            property_type,
            address,
            area,
            university_nearby,
            distance_km,
            rent_amount,
            deposit_amount,
            utilities_desc,
            gender_policy,
            availability_date,
            photos,
            lat,
            lng,
            facilities,
            is_verified,
            is_flagged
        )
        VALUES (
            ?, ?, ?, ?, ?, ?, ?,
            0.6,
            ?, ?,
            'Shared electricity token',
            ?,
            date('now', '+7 days'),
            ?,
            23.7400,
            90.3850,
            ?,
            1,
            0
        )
        """,
        (
            owner_id,
            title,
            description,
            property_type,
            address,
            area,
            university_nearby,
            rent_amount,
            deposit_amount,
            gender_policy,
            sample_photos,
            json.dumps(facs)
        )
    )

    conn.commit()
    conn.close()

    return JSONResponse({
        "status": "success",
        "message": "Listing published successfully."
    })




# -------------------- ADMIN REPORT ACTION --------------------

def require_admin(request: Request):

    user = get_current_user(request)

    if user["role"] != "admin":
        raise HTTPException(
            status_code=403,
            detail="Admin only."
        )

    source = (
        request.headers.get("origin")
        or request.headers.get("referer")
    )

    if not source:
        raise HTTPException(
            status_code=403,
            detail="Missing request origin."
        )

    parsed = urlsplit(source)

    if (
        parsed.scheme,
        parsed.netloc
    ) != (
        request.url.scheme,
        request.url.netloc
    ):
        raise HTTPException(
            status_code=403,
            detail="Cross-site request blocked."
        )

    return user


@app.post("/api/admin-report-action")
async def api_admin_report_action(
    request: Request,
    report_id: int = Form(...),
    listing_id: int = Form(...),
    action: str = Form(...)
):

    require_admin(request)

    if action not in {"takedown", "dismiss"}:
        raise HTTPException(
            status_code=422,
            detail="Invalid report action."
        )

    conn = get_db()

    try:
        report = conn.execute(
            """
            SELECT listing_id
            FROM reports
            WHERE id = ? AND status = 'pending'
            """,
            (report_id,)
        ).fetchone()

        if (
            report is None
            or report["listing_id"] != listing_id
        ):
            raise HTTPException(
                status_code=404,
                detail="Pending report not found."
            )

        status = (
            "taken_down"
            if action == "takedown"
            else "dismissed"
        )

        conn.execute(
            """
            UPDATE reports
            SET status = ?
            WHERE id = ?
            """,
            (status, report_id)
        )

        if action == "takedown":

            # Soft takedown keeps related records.
            conn.execute(
                """
                UPDATE listings
                SET
                    is_flagged = 1,
                    flag_reason = 'Removed by admin',
                    is_verified = 0
                WHERE id = ?
                  AND COALESCE(flag_reason, '')
                      != 'Removed by owner'
                """,
                (listing_id,)
            )

        else:

            # Keep flagged if other reports are pending.
            conn.execute(
                """
                UPDATE listings
                SET
                    is_flagged = 0,
                    flag_reason = NULL
                WHERE id = ?
                  AND COALESCE(flag_reason, '')
                      != 'Removed by owner'
                  AND COALESCE(flag_reason, '')
                      != 'Removed by admin'
                  AND NOT EXISTS (
                      SELECT 1
                      FROM reports
                      WHERE listing_id = ?
                        AND status = 'pending'
                  )
                """,
                (listing_id, listing_id)
            )

        conn.commit()

    finally:
        conn.close()

    return {
        "status": "success",
        "message": "Admin report action saved."
    }


# -------------------- ADMIN PROPERTY VERIFICATION --------------------

@app.post("/api/admin-toggle-verify")
async def api_admin_toggle_verify(
    request: Request,
    listing_id: int = Form(...),
    is_verified: int = Form(...)
):

    require_admin(request)

    if is_verified not in (0, 1):
        raise HTTPException(
            status_code=422,
            detail="Invalid verification value."
        )

    conn = get_db()

    try:
        listing = conn.execute("SELECT * FROM listings WHERE id=?",(listing_id,)).fetchone()
        if not listing or listing['is_flagged']:
            raise HTTPException(404,"Active listing not found.")
        if is_verified and not (listing['owner_identity_checked'] and listing['inspection_completed']):
            raise HTTPException(409,"Complete owner identity and property inspection checklist first.")
        cursor = conn.execute(
            """UPDATE listings SET is_verified=? WHERE id=? AND is_flagged=0""",
            (is_verified, listing_id)
        )
        if is_verified:
            create_search_alerts(conn,listing_id)

        if cursor.rowcount != 1:
            raise HTTPException(
                status_code=404,
                detail="Active listing not found."
            )

        conn.commit()

    finally:
        conn.close()

    return {
        "status": "success",
        "message": "Verification status updated."
    }


# ============================================================
# RUN APPLICATION
# ============================================================

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
