
import json
import io
import re
import secrets
from pathlib import Path

from PIL import Image, ImageOps, UnidentifiedImageError
from contextlib import closing
from datetime import date, datetime, timezone
from urllib.parse import urlsplit

from fastapi import APIRouter, HTTPException, Request, UploadFile, File

from app.auth import (
    SESSION_COOKIE_NAME,
    get_user_by_session
)
from app.database import get_db


router = APIRouter(
    prefix="/api/landlord",
    tags=["Landlord"]
)

REMOVED_REASON = "Removed by owner"
PHOTO_ROOT = Path(__file__).resolve().parents[1] / "static" / "uploads" / "users"
MAX_UPLOAD_BYTES = 5 * 1024 * 1024
MAX_UPLOAD_PIXELS = 24_000_000
MAX_OWNER_PHOTOS = 100
_LOCAL_IMAGE = re.compile(r"^/static/uploads/users/([0-9]+)/([a-f0-9]{32}\.jpg)$")


def _validated_image_url(url: str, owner_id: int | None = None):
    """Accept HTTP(S) URLs or only this landlord's own uploaded images."""
    if not url or len(url) > 1500:
        raise HTTPException(422, "Invalid image URL.")
    if url.startswith("/static/uploads/"):
        match = _LOCAL_IMAGE.fullmatch(url)
        if not match or owner_id is None or int(match.group(1)) != owner_id:
            raise HTTPException(422, "The uploaded photo does not belong to this account.")
        if not (PHOTO_ROOT / str(owner_id) / match.group(2)).is_file():
            raise HTTPException(422, "Uploaded photo not found. Please upload it again.")
        return url
    parsed = urlsplit(url)
    if parsed.scheme not in {"https", "http"} or not parsed.netloc:
        raise HTTPException(422, "Enter a valid HTTP(S) image URL.")
    return url


@router.post('/photos/upload')
async def upload_photo(request: Request, file: UploadFile = File(...)):
    """Authenticated landlord-only image upload with content validation.

    Images are decoded and re-encoded to JPEG, removing metadata and
    preventing SVG/script uploads. Uploaded photos remain unverified until
    their listing is approved by the administrator.
    """
    _check_same_origin(request)
    user = _landlord(request)
    owner_id = int(user['id'])

    # Reading a maximum N+1 bytes bounds request memory use.
    raw = await file.read(MAX_UPLOAD_BYTES + 1)
    await file.close()
    if not raw or len(raw) > MAX_UPLOAD_BYTES:
        raise HTTPException(413, 'Maximum photo size is 5 MB.')

    try:
        with Image.open(io.BytesIO(raw)) as source:
            if source.format not in {'JPEG', 'PNG', 'WEBP'}:
                raise HTTPException(415, 'Only JPG, PNG and WebP images are allowed.')
            if source.width * source.height > MAX_UPLOAD_PIXELS:
                raise HTTPException(413, 'Image resolution is too large.')
            # Decode fully before writing; never store original uploaded bytes.
            source.load()
            image = ImageOps.exif_transpose(source)
            image.thumbnail((1800, 1800), Image.Resampling.LANCZOS)
            if image.mode == 'RGBA' or 'transparency' in image.info:
                rgba = image.convert('RGBA')
                background = Image.new('RGB', rgba.size, 'white')
                background.paste(rgba, mask=rgba.getchannel('A'))
                image = background
            else:
                image = image.convert('RGB')
            output = io.BytesIO()
            image.save(output, 'JPEG', quality=84, optimize=True)
            content = output.getvalue()
    except HTTPException:
        raise
    except (UnidentifiedImageError, OSError, ValueError, Image.DecompressionBombError):
        raise HTTPException(422, 'This image cannot be processed. Choose a valid photo.')

    owner_folder = PHOTO_ROOT / str(owner_id)
    owner_folder.mkdir(parents=True, exist_ok=True)
    if sum(1 for _ in owner_folder.glob('*.jpg')) >= MAX_OWNER_PHOTOS:
        raise HTTPException(429, 'Photo limit reached. Contact the administrator.')
    photo_name = secrets.token_hex(16) + '.jpg'
    destination = owner_folder / photo_name
    # Exclusive creation prevents overwriting an existing file.
    with destination.open('xb') as saved:
        saved.write(content)
    return {'ok': True,
            'url': f'/static/uploads/users/{owner_id}/{photo_name}',
            'message': 'Photo uploaded successfully.'}


ALLOWED_TYPES = {
    "Mess Seat",
    "Single Room",
    "Bachelor Flat",
    "Hostel Seat"
}

ALLOWED_GENDERS = {
    "Male Only",
    "Female Only",
    "Any"
}

FACILITY_FIELDS = {
    "fac_wifi": "wifi",
    "fac_gen": "generator",
    "fac_water": "water_247",
    "fac_meals": "meals",
    "fac_bath": "attached_bath",
    "fac_lift": "lift"
}


# ==================================================
# SECURITY HELPERS
# ==================================================

def _landlord(request: Request):
    token = request.cookies.get(
        SESSION_COOKIE_NAME
    )

    user = get_user_by_session(token)

    if not user:
        raise HTTPException(
            status_code=401,
            detail="Please sign in first."
        )

    if user["role"] != "landlord":
        raise HTTPException(
            status_code=403,
            detail="Only landlords can perform this action."
        )

    return user


def _check_same_origin(request: Request):
    """
    Block cross-site form submissions.
    """

    source = (
        request.headers.get("origin")
        or request.headers.get("referer")
    )

    if not source:
        raise HTTPException(
            status_code=403,
            detail="Missing request origin."
        )

    url = urlsplit(source)

    if (
        url.scheme,
        url.netloc
    ) != (
        request.url.scheme,
        request.url.netloc
    ):
        raise HTTPException(
            status_code=403,
            detail="Cross-site request blocked."
        )


# ==================================================
# VALIDATION HELPERS
# ==================================================

def _number(
    value,
    name,
    minimum,
    maximum,
    float_type=False
):
    try:
        num = (
            float(value)
            if float_type
            else int(value)
        )

    except (ValueError, TypeError, OverflowError):
        raise HTTPException(
            status_code=422,
            detail=f"Invalid {name}."
        )

    if not minimum <= num <= maximum:
        raise HTTPException(
            status_code=422,
            detail=(
                f"{name} must be between "
                f"{minimum} and {maximum}."
            )
        )

    return num


def _text(
    form,
    key,
    label,
    minimum=1,
    maximum=500
):
    value = str(
        form.get(key, "")
    ).strip()

    if not minimum <= len(value) <= maximum:
        raise HTTPException(
            status_code=422,
            detail=(
                f"{label} must contain "
                f"{minimum}-{maximum} characters."
            )
        )

    return value


def _listing_data(form, owner_id):

    property_type = _text(
        form, "property_type", "Property type", 1, 60
    )

    gender_policy = _text(
        form, "gender_policy", "Gender policy", 1, 30
    )

    if (
        property_type not in ALLOWED_TYPES
        or gender_policy not in ALLOWED_GENDERS
    ):
        raise HTTPException(
            status_code=422,
            detail="Invalid property type or gender policy."
        )

    availability_date = _text(
        form,
        "availability_date",
        "Availability date",
        10,
        10
    )

    try:
        date.fromisoformat(availability_date)

    except ValueError:
        raise HTTPException(
            status_code=422,
            detail="Invalid availability date."
        )

    photo_url = str(
        form.get("photo_url", "")
    ).strip()

    if photo_url:
        photo_url = _validated_image_url(photo_url, owner_id)
    else:
        photo_url = (
            'https://images.unsplash.com/'
            'photo-1555854877-bab0e564b8d5?w=800'
        )

    extra_urls = []
    for candidate in str(form.get('additional_photo_urls', '')).splitlines():
        candidate = candidate.strip()
        if candidate:
            extra_urls.append(_validated_image_url(candidate, owner_id))
    if len(extra_urls) > 4:
        raise HTTPException(422, 'Maximum four additional photos.')

    facilities = [
        value
        for key, value in FACILITY_FIELDS.items()
        if form.get(key)
    ]

    return {
        "title": _text(
            form, "title", "Title", 5, 150
        ),
        "title_bn": _text(form, 'title_bn','Bangla title',0,150),
        "description_bn": _text(form, 'description_bn','Bangla description',0,2000),

        "description": _text(
            form, "description", "Description", 10, 2000
        ),

        "property_type": property_type,

        "address": _text(
            form, "address", "Address", 5, 400
        ),

        "area": _text(
            form, "area", "Area", 2, 100
        ),

        "university_nearby": _text(
            form,
            "university_nearby",
            "Nearby university",
            2,
            150
        ),

        "distance_km": _number(
            form.get("distance_km"),
            "Distance",
            0,
            100,
            True
        ),

        "rent_amount": _number(
            form.get("rent_amount"),
            "Rent",
            1,
            500000
        ),

        "deposit_amount": _number(
            form.get("deposit_amount"),
            "Deposit",
            0,
            1000000
        ),

        "utilities_desc": str(
            form.get("utilities_desc", "")
        ).strip()[:500],

        "gender_policy": gender_policy,

        "availability_date": availability_date,

        "photos": json.dumps(
            [photo_url] + extra_urls
        ),

        "lat": _number(
            form.get("lat"),
            "Latitude",
            20,
            27,
            True
        ),

        "lng": _number(
            form.get("lng"),
            "Longitude",
            88,
            93,
            True
        ),

        "facilities": json.dumps(
            facilities
        )
    }


# ==================================================
# CREATE PROPERTY
# ==================================================

@router.post("/create")
async def create_listing(request: Request):

    _check_same_origin(request)

    user = _landlord(request)

    fields = _listing_data(
        await request.form(), int(user["id"])
    )

    # Never trust owner_id from the browser.
    fields["owner_id"] = user["id"]

    # Admin approval is required.
    fields["is_verified"] = 0

    with closing(get_db()) as conn, conn:

        cursor = conn.execute(
            """
            INSERT INTO listings (
                owner_id,
                title,
                title_bn,
                description,
                description_bn,
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
                is_verified
            )
            VALUES (
                :owner_id,
                :title,
                :title_bn,
                :description,
                :description_bn,
                :property_type,
                :address,
                :area,
                :university_nearby,
                :distance_km,
                :rent_amount,
                :deposit_amount,
                :utilities_desc,
                :gender_policy,
                :availability_date,
                :photos,
                :lat,
                :lng,
                :facilities,
                :is_verified
            )
            """,
            fields
        )

        listing_id = cursor.lastrowid

    return {
        "ok": True,
        "listing_id": listing_id,
        "status": "pending_verification"
    }


# ==================================================
# EDIT PROPERTY
# ==================================================

@router.post("/update")
async def update_listing(request: Request):

    _check_same_origin(request)

    user = _landlord(request)

    form = await request.form()

    listing_id = _number(
        form.get("listing_id"),
        "Listing ID",
        1,
        100000000
    )

    fields = _listing_data(form, int(user["id"]))

    fields["listing_id"] = listing_id
    fields["owner_id"] = user["id"]

    with closing(get_db()) as conn, conn:

        cursor = conn.execute(
            """
            UPDATE listings

            SET
                title = :title,
                title_bn = :title_bn,
                description = :description,
                description_bn = :description_bn,
                property_type = :property_type,
                address = :address,
                area = :area,
                university_nearby = :university_nearby,
                distance_km = :distance_km,
                rent_amount = :rent_amount,
                deposit_amount = :deposit_amount,
                utilities_desc = :utilities_desc,
                gender_policy = :gender_policy,
                availability_date = :availability_date,
                photos = :photos,
                lat = :lat,
                lng = :lng,
                facilities = :facilities,
                is_verified = 0,
                inspection_completed = 0

            WHERE id = :listing_id
              AND owner_id = :owner_id
              AND COALESCE(flag_reason, '') != 'Removed by owner'
            """,
            fields
        )

        if cursor.rowcount != 1:
            raise HTTPException(
                status_code=404,
                detail="Your active listing was not found."
            )

    return {
        "ok": True,
        "status": "pending_verification"
    }


# ==================================================
# REMOVE PROPERTY
# ==================================================

@router.post("/remove")
async def remove_listing(request: Request):

    _check_same_origin(request)

    user = _landlord(request)

    form = await request.form()

    listing_id = _number(
        form.get("listing_id"),
        "Listing ID",
        1,
        100000000
    )

    # Soft removal: keep previous booking/review history.
    # Public listing queries must exclude is_flagged=1.

    with closing(get_db()) as conn, conn:

        cursor = conn.execute(
            """
            UPDATE listings

            SET
                is_flagged = 1,
                flag_reason = ?,
                is_verified = 0

            WHERE id = ?
              AND owner_id = ?
              AND COALESCE(flag_reason, '') != ?
            """,
            (
                REMOVED_REASON,
                listing_id,
                user["id"],
                REMOVED_REASON
            )
        )

        if cursor.rowcount != 1:
            raise HTTPException(
                status_code=404,
                detail="Your active listing was not found."
            )

    return {
        "ok": True,
        "message": "Listing removed from public view."
    }


# ==================================================
# CONFIRM STUDENT VISIT
# ==================================================

@router.post("/visit-status")
async def update_visit(request: Request):

    _check_same_origin(request)

    user = _landlord(request)

    form = await request.form()

    visit_id = _number(
        form.get("visit_id"),
        "Visit ID",
        1,
        100000000
    )

    proposed_day = str(form.get('visit_date','')).strip()
    slot = str(form.get('time_slot','')).strip()
    from datetime import date as Date
    if proposed_day:
        try: proposed = Date.fromisoformat(proposed_day)
        except ValueError: raise HTTPException(422,'Invalid visit date.')
        if proposed < Date.today(): raise HTTPException(422,'Cannot schedule a past date.')
    if slot and (len(slot)>80 or len(slot)<3):raise HTTPException(422,'Invalid time slot.')
    with closing(get_db()) as conn, conn:

        cursor = conn.execute(
            """
            UPDATE visits_and_bookings

            SET status = 'visit_scheduled',
                visit_date = COALESCE(NULLIF(?,''),visit_date),
                time_slot = COALESCE(NULLIF(?,''),time_slot)

            WHERE id = ?
              AND owner_id = ?
              AND status = 'visit_requested'

              AND EXISTS (
                  SELECT 1
                  FROM listings l
                  WHERE l.id = visits_and_bookings.listing_id
                    AND l.owner_id = ?
              )
            """,
            (
                proposed_day,slot,
                visit_id,
                user["id"],
                user["id"]
            )
        )

        if cursor.rowcount != 1:
            raise HTTPException(
                status_code=404,
                detail="Pending visit request was not found."
            )

    return {"ok": True}


# ==================================================
# RESOLVE MAINTENANCE
# ==================================================

@router.post("/maintenance-status")
async def resolve_maintenance(request: Request):
    _check_same_origin(request)
    user = _landlord(request)
    form = await request.form()
    ticket_id = _number(form.get("ticket_id"), "Ticket ID", 1, 100000000)
    status = str(form.get("status", "resolved"))
    if status not in {"in_progress", "resolved"}:
        raise HTTPException(status_code=422, detail="Invalid maintenance status.")
    previous_status = "open" if status == "in_progress" else "in_progress"
    now = datetime.now(timezone.utc).isoformat() if status == "resolved" else None
    with closing(get_db()) as conn, conn:
        cursor = conn.execute("""UPDATE maintenance_requests
            SET status=?, resolved_at=?
            WHERE id=? AND owner_id=? AND status=?
              AND EXISTS(SELECT 1 FROM listings l
                WHERE l.id = maintenance_requests.listing_id AND l.owner_id=?)""",
            (status,now,ticket_id,user["id"],previous_status,user["id"]))
        if cursor.rowcount != 1:
            raise HTTPException(status_code=404, detail="This maintenance ticket is not at the required stage.")
    return {"ok": True, "status":status}
