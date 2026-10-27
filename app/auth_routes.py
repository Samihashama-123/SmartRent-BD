
import hmac
import os
import secrets
import hashlib
import smtplib
import ssl
from datetime import datetime, timedelta, timezone
from email.message import EmailMessage
from urllib.parse import urlsplit
from dotenv import load_dotenv

from fastapi import APIRouter, Request, Form, HTTPException
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

from app.auth import (
    SESSION_COOKIE_NAME,
    SESSION_DURATION_DAYS,
    authenticate_user,
    register_user,
    create_session,
    get_user_by_session,
    delete_session,
    hash_password
)
from app.i18n import DEFAULT_LANGUAGE, get_language
from app.database import get_db


router = APIRouter()

BASE_DIR = os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)

templates = Jinja2Templates(
    directory=os.path.join(BASE_DIR, "templates")
)

# Read private settings from this project's .env, not from GitHub.
# Explicit system environment variables take precedence over the file.
load_dotenv(os.path.join(BASE_DIR, '.env'), override=False)

CSRF_COOKIE_NAME = "smartrent_csrf"


# --------------------------------------------------
# AUTHENTICATION FORM HELPERS
# --------------------------------------------------

def get_language_from_request(request: Request):
    return get_language(
        request.cookies.get(
            "smartrent_lang",
            DEFAULT_LANGUAGE
        )
    )


def render_auth(
    request: Request,
    mode: str,
    error: str = "",
    values: dict = None,
    status_code: int = 200
):
    csrf_token = request.cookies.get(CSRF_COOKIE_NAME)

    if not csrf_token or len(csrf_token) > 128:
        csrf_token = secrets.token_urlsafe(32)

    response = templates.TemplateResponse(
        request=request,
        name="auth.html",
        context={
            "lang": get_language_from_request(request),
            "mode": mode,
            "error": error,
            "values": values or {},
            "csrf_token": csrf_token
        },
        status_code=status_code
    )

    response.set_cookie(
        key=CSRF_COOKIE_NAME,
        value=csrf_token,
        max_age=60 * 60 * 24,
        httponly=True,
        secure=request.url.scheme == "https",
        samesite="lax",
        path="/"
    )

    response.headers["Cache-Control"] = "no-store"

    return response


def verify_csrf(request: Request, submitted_token: str):
    cookie_token = request.cookies.get(CSRF_COOKIE_NAME, "")

    if (
        not submitted_token
        or not cookie_token
        or not hmac.compare_digest(
            submitted_token,
            cookie_token
        )
    ):
        raise HTTPException(
            status_code=403,
            detail="Invalid form security token."
        )


def already_logged_in(request: Request):
    return get_user_by_session(
        request.cookies.get(SESSION_COOKIE_NAME)
    )


def safe_next(value: str):
    if not value or not value.startswith('/') or value.startswith('//') or '\\' in value or '\r' in value or '\n' in value:
        return '/'
    return value


def destination_for_role(role: str) -> str:
    return {'admin': '/admin', 'landlord': '/landlord', 'student': '/profile'}.get(role, '/')


def login_response(request: Request, user_id: int, next_url: str = ''):
    # If a guest followed a protected link, return them there. Otherwise
    # send each role directly to the dashboard that actually belongs to them.
    with get_db() as conn:
        row = conn.execute('SELECT role FROM users WHERE id=?', (user_id,)).fetchone()
    destination = safe_next(next_url) if next_url else destination_for_role(row['role'] if row else '')
    token = create_session(user_id)

    response = RedirectResponse(
        url=destination,
        status_code=303
    )

    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=token,
        max_age=SESSION_DURATION_DAYS * 24 * 60 * 60,
        httponly=True,
        secure=request.url.scheme == "https",
        samesite="lax",
        path="/"
    )

    response.headers["Cache-Control"] = "no-store"

    return response


# --------------------------------------------------
# LOGIN PAGE
# --------------------------------------------------

@router.get('/admin/login')
async def admin_login_entry():
    """Optional staff URL; authenticates on the same secure login page."""
    return RedirectResponse('/login?next=/admin', status_code=303)


@router.get("/login")
async def login_page(request: Request, next: str = ''):
    member = already_logged_in(request)
    if member:
        return RedirectResponse(safe_next(next) if next else destination_for_role(member['role']), status_code=303)

    return render_auth(
        request=request,
        mode="login",
        values={"next": safe_next(next) if next else ''}
    )


@router.post("/login")
async def login_submit(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    csrf_token: str = Form(...),
    next: str = Form('')
):
    verify_csrf(request, csrf_token)

    user = authenticate_user(email, password)

    if not user:
        return render_auth(
            request=request,
            mode="login",
            error="invalid_credentials",
            values={"email": email, "next": safe_next(next) if next else ''},
            status_code=400
        )

    return login_response(request, user["id"], next)


# --------------------------------------------------
# REGISTRATION PAGE
# --------------------------------------------------

@router.get("/register")
async def register_page(request: Request):
    if already_logged_in(request):
        return RedirectResponse("/", status_code=303)

    return render_auth(
        request=request,
        mode="register"
    )


@router.post("/register")
async def register_submit(
    request: Request,
    name: str = Form(...),
    email: str = Form(...),
    phone: str = Form(...),
    role: str = Form(...),
    password: str = Form(...),
    confirm_password: str = Form(...),
    csrf_token: str = Form(...),
    university: str = Form(""),
    department: str = Form("")
):
    verify_csrf(request, csrf_token)

    values = {
        "name": name,
        "email": email,
        "phone": phone,
        "role": role,
        "university": university,
        "department": department
    }

    if password != confirm_password:
        return render_auth(
            request=request,
            mode="register",
            error="password_mismatch",
            values=values,
            status_code=400
        )

    try:
        user = register_user(
            name=name,
            email=email,
            phone=phone,
            password=password,
            role=role,
            university=university,
            department=department
        )

    except ValueError as error:
        message = str(error)

        if "already exists" in message:
            error_code = "email_exists"
        elif "Password" in message:
            error_code = "invalid_password"
        elif "role" in message.lower():
            error_code = "invalid_role"
        else:
            error_code = "invalid_information"

        return render_auth(
            request=request,
            mode="register",
            error=error_code,
            values=values,
            status_code=400
        )

    return login_response(request, user["id"])


# --------------------------------------------------
# LOGOUT PAGE
# --------------------------------------------------

@router.get("/logout")
async def logout_page(request: Request):
    if not already_logged_in(request):
        return RedirectResponse("/login", status_code=303)

    return render_auth(
        request=request,
        mode="logout"
    )


@router.post("/logout")
async def logout_submit(
    request: Request,
    csrf_token: str = Form(...)
):
    verify_csrf(request, csrf_token)

    token = request.cookies.get(SESSION_COOKIE_NAME)

    if token:
        delete_session(token)

    response = RedirectResponse(
        url="/login",
        status_code=303
    )

    response.delete_cookie(
        key=SESSION_COOKIE_NAME,
        path="/"
    )

    return response


# --------------------------------------------------
# PASSWORD RECOVERY — EMAIL BASED, ONE USE, EXPIRING
# --------------------------------------------------

def _recovery_page(request: Request, mode: str, message: str = '', token: str = '', status: int = 200):
    csrf = request.cookies.get(CSRF_COOKIE_NAME)
    if not csrf or len(csrf) > 128:
        csrf = secrets.token_urlsafe(32)
    response = templates.TemplateResponse(
        request=request,
        name='password_recovery.html',
        context={
            'lang': get_language_from_request(request),
            'mode': mode,
            'message': message,
            'token': token,
            'csrf_token': csrf,
            'mail_ready': bool(os.getenv('SMARTRENT_SMTP_HOST') and os.getenv('SMARTRENT_SMTP_FROM'))
        },
        status_code=status
    )
    response.set_cookie(CSRF_COOKIE_NAME, csrf, max_age=86400, httponly=True,
                        secure=request.url.scheme=='https', samesite='lax',path='/')
    response.headers['Cache-Control']='no-store'
    return response


def _utcnow():
    return datetime.now(timezone.utc)


def _smtp_send_reset(email: str, link: str):
    host = os.getenv('SMARTRENT_SMTP_HOST','').strip()
    sender = os.getenv('SMARTRENT_SMTP_FROM','').strip()
    if not host or not sender:
        raise RuntimeError('Email delivery is not configured.')
    port = int(os.getenv('SMARTRENT_SMTP_PORT','587'))
    user = os.getenv('SMARTRENT_SMTP_USER','')
    password = os.getenv('SMARTRENT_SMTP_PASSWORD','')
    msg=EmailMessage()
    msg['Subject']='SmartRent BD — reset your password'
    msg['From']=sender
    msg['To']=email
    msg.set_content('A password reset was requested for SmartRent BD.\n\n'
        'Use this one-time link within 30 minutes:\n'+link+'\n\n'
        'If this was not you, ignore this email. No password has changed.')
    context=ssl.create_default_context()
    if port == 465:
        with smtplib.SMTP_SSL(host, port, timeout=10, context=context) as smtp:
            if user: smtp.login(user,password)
            smtp.send_message(msg)
    else:
        with smtplib.SMTP(host, port, timeout=10) as smtp:
            smtp.ehlo(); smtp.starttls(context=context); smtp.ehlo()
            if user: smtp.login(user,password)
            smtp.send_message(msg)


@router.get('/forgot-password')
async def forgot_password_page(request:Request):
    return _recovery_page(request,'forgot')


@router.post('/forgot-password')
async def forgot_password_submit(request:Request,email:str=Form(...),csrf_token:str=Form(...)):
    verify_csrf(request,csrf_token)
    email=(email or '').strip().lower()
    # Fail transparently when no actual delivery mechanism is installed.
    if not os.getenv('SMARTRENT_SMTP_HOST') or not os.getenv('SMARTRENT_SMTP_FROM'):
        return _recovery_page(request,'forgot','not_configured',status=503)
    # Always give the same public-facing result regardless of account existence.
    generic='sent_if_exists'
    now=_utcnow()
    with get_db() as conn:
        conn.execute('DELETE FROM password_reset_tokens WHERE expires_at < ?', (now.isoformat(),))
        row=conn.execute('SELECT id,email FROM users WHERE lower(email)=? AND is_active=1 AND password_hash IS NOT NULL',
             (email,)).fetchone()
        if not row:
            return _recovery_page(request,'forgot',generic)
        recent=conn.execute('SELECT created_at FROM password_reset_tokens WHERE user_id=? ORDER BY id DESC LIMIT 1',(row['id'],)).fetchone()
        if recent and datetime.fromisoformat(recent['created_at'])>now-timedelta(minutes=2):
            return _recovery_page(request,'forgot',generic)
        token=secrets.token_urlsafe(36)
        hashed=hashlib.sha256(token.encode()).hexdigest()
        conn.execute('INSERT INTO password_reset_tokens (user_id,token_hash,created_at,expires_at) VALUES (?,?,?,?)',
                     (row['id'],hashed,now.isoformat(),(now+timedelta(minutes=30)).isoformat()))
        conn.commit()
        base=os.getenv('SMARTRENT_PUBLIC_URL','http://127.0.0.1:8000').strip().rstrip('/')
        # URL from trusted environment, never from user-controlled Host header.
        if not base.startswith(('https://','http://')):
            conn.execute('DELETE FROM password_reset_tokens WHERE token_hash=?',(hashed,));conn.commit()
            return _recovery_page(request,'forgot','delivery_failed',status=503)
        link=base+'/reset-password?token='+token
        try:
            _smtp_send_reset(row['email'],link)
        except (smtplib.SMTPException,OSError,RuntimeError,ValueError):
            conn.execute('DELETE FROM password_reset_tokens WHERE token_hash=?',(hashed,));conn.commit()
            return _recovery_page(request,'forgot','delivery_failed',status=503)
    return _recovery_page(request,'forgot',generic)


@router.get('/reset-password')
async def reset_password_page(request:Request,token:str=''):
    if len(token)>200 or len(token)<24:
        return _recovery_page(request,'reset','invalid_token',status=400)
    hashed=hashlib.sha256(token.encode()).hexdigest()
    with get_db() as conn:
        row=conn.execute('SELECT id FROM password_reset_tokens WHERE token_hash=? AND expires_at>?',
            (hashed,_utcnow().isoformat())).fetchone()
    if not row:
        return _recovery_page(request,'reset','invalid_token',status=400)
    return _recovery_page(request,'reset',token=token)


@router.post('/reset-password')
async def reset_password_submit(request:Request,token:str=Form(...),password:str=Form(...),
                                confirm_password:str=Form(...),csrf_token:str=Form(...)):
    verify_csrf(request,csrf_token)
    if password!=confirm_password:
        return _recovery_page(request,'reset','password_mismatch',token=token,status=400)
    try:
        digest=hash_password(password)
    except ValueError:
        return _recovery_page(request,'reset','weak_password',token=token,status=400)
    if len(token)>200 or len(token)<24:
        return _recovery_page(request,'reset','invalid_token',status=400)
    hashed=hashlib.sha256(token.encode()).hexdigest()
    with get_db() as conn:
        row=conn.execute('SELECT user_id FROM password_reset_tokens WHERE token_hash=? AND expires_at>?',
            (hashed,_utcnow().isoformat())).fetchone()
        if not row:
            return _recovery_page(request,'reset','invalid_token',status=400)
        conn.execute('UPDATE users SET password_hash=? WHERE id=?',(digest,row['user_id']))
        conn.execute('DELETE FROM password_reset_tokens WHERE user_id=?',(row['user_id'],))
        conn.execute('DELETE FROM auth_sessions WHERE user_id=?',(row['user_id'],))
        conn.commit()
    return _recovery_page(request,'complete','password_updated')
