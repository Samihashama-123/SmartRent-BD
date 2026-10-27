"""v5: public browsing, private role navigation and real password recovery."""
import importlib
from pathlib import Path
from urllib.parse import urlsplit, parse_qs

from fastapi.testclient import TestClient


def test_public_guest_and_role_menus(tmp_path,monkeypatch):
    from app import database, auth
    from main import app
    monkeypatch.setattr(database,'DB_PATH',str(tmp_path/'new.sqlite'))
    with TestClient(app,follow_redirects=False) as client:
        for url in ('/','/listings'):
            resp=client.get(url)
            assert resp.status_code==200, (url,resp.text[:300])
            assert 'href="/login"' in resp.text
            assert '/register' in resp.text
            assert 'href="/mess-manager"' not in resp.text
        assert client.get('/maintenance').status_code==303
        assert client.get('/roommates').status_code==303
        assert client.get('/forgot-password').status_code==200
        assert 'Forgot password?' in client.get('/login').text

        student=auth.register_user('Student QA','studentqa@example.com','01711111111','password-876',role='student')
        landlord=auth.register_user('Landlord QA','landlordqa@example.com','01711111112','password-876',role='landlord')
        with database.get_db() as conn:
            conn.execute('INSERT INTO users(name,email,phone,role,password_hash,is_active) VALUES(?,?,?,?,?,1)',
                ('Admin QA','adminqa@example.com','01711111113','admin',auth.hash_password('password-876')))
            admin=conn.execute("SELECT id FROM users WHERE email='adminqa@example.com'").fetchone()['id']

        for identity, role in [(student,'student'),(landlord,'landlord'),({'id':admin},'admin')]:
            token=auth.create_session(identity['id'])
            client.cookies.set(auth.SESSION_COOKIE_NAME,token)
            html=client.get('/').text
            assert '/profile' in html
            if role=='student':
                assert 'href="/mess-manager"' in html
                assert 'href="/my-bookings"' in html
                assert 'href="/landlord"' not in html
            elif role=='landlord':
                assert 'href="/landlord"' in html
                assert 'href="/mess-manager"' not in html
                assert 'href="/roommates"' not in html
                assert 'href="/my-bookings"' not in html
            else:
                assert 'href="/admin"' in html
                assert 'href="/mess-manager"' not in html
                assert 'href="/maintenance"' not in html
                assert 'href="/landlord"' not in html
                assert 'href="/roommates"' not in html
            client.cookies.delete(auth.SESSION_COOKIE_NAME)


def test_one_time_password_reset_without_exposing_token(tmp_path,monkeypatch):
    from app import database, auth, auth_routes
    from main import app
    monkeypatch.setattr(database,'DB_PATH',str(tmp_path/'pwd.sqlite'))
    monkeypatch.setenv('SMARTRENT_SMTP_HOST','mail.example.com')
    monkeypatch.setenv('SMARTRENT_SMTP_FROM','noreply@example.com')
    monkeypatch.setenv('SMARTRENT_PUBLIC_URL','http://127.0.0.1:8000')
    sent=[]
    monkeypatch.setattr(auth_routes,'_smtp_send_reset',lambda email,link:sent.append((email,link)))
    with TestClient(app,follow_redirects=False) as c:
        user=auth.register_user('Recovery User','recover@example.com','01722222222','initial-pwd',role='student')
        form=c.get('/forgot-password')
        csrf=c.cookies.get('smartrent_csrf')
        assert form.status_code==200 and csrf
        resp=c.post('/forgot-password',data={'email':'recover@example.com','csrf_token':csrf})
        assert resp.status_code==200 and len(sent)==1
        token=parse_qs(urlsplit(sent[0][1]).query)['token'][0]
        assert token not in resp.text
        assert c.get('/reset-password?token='+token).status_code==200
        csrf=c.cookies.get('smartrent_csrf')
        result=c.post('/reset-password',data={'csrf_token':csrf,'token':token,'password':'another-new-password','confirm_password':'another-new-password'})
        assert result.status_code==200 and 'Password updated' in result.text
        assert auth.authenticate_user('recover@example.com','initial-pwd') is None
        assert auth.authenticate_user('recover@example.com','another-new-password')
        assert c.get('/reset-password?token='+token).status_code==400
        assert c.post('/reset-password',data={'csrf_token':csrf,'token':token,'password':'again-new-password','confirm_password':'again-new-password'}).status_code==400
