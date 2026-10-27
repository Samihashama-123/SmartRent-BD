"""v6: ensure admin routing, role menus, SMTP transparency and safety design."""
from pathlib import Path
from fastapi.testclient import TestClient
from app import auth, database
from main import app


def _csrf_login(c, email, password):
    login = c.get('/login', follow_redirects=False)
    assert login.status_code == 200
    token = c.cookies.get('smartrent_csrf')
    assert token
    return c.post('/login', data={
        'email':email, 'password':password, 'csrf_token':token, 'next':''
    }, follow_redirects=False)


def test_role_redirects_and_access(tmp_path, monkeypatch):
    monkeypatch.setattr(database, 'DB_PATH', str(tmp_path/'auth_roles.sqlite'))
    with TestClient(app, follow_redirects=False) as c:
        password='final-Test-password-123!'
        student = auth.register_user('Student','final.student@example.test','01711111111',password,role='student')
        landlord = auth.register_user('Landlord','final.landlord@example.test','01711111112',password,role='landlord')
        with database.get_db() as db:
            db.execute("INSERT INTO users(name,email,phone,role,password_hash,is_active) VALUES(?,?,?,?,?,1)",
                       ('Admin','final.admin@example.test','01711111113','admin',auth.hash_password(password)))
            db.commit()

        redirect = c.get('/admin/login', follow_redirects=False)
        assert redirect.status_code == 303 and redirect.headers['location']=='/login?next=/admin'
        for role, target in [('student','/profile'),('landlord','/landlord'),('admin','/admin')]:
            c.cookies.delete(auth.SESSION_COOKIE_NAME)
            res = _csrf_login(c, f'final.{role}@example.test', password)
            assert res.status_code == 303 and res.headers['location']==target
            actual=c.get(target)
            assert actual.status_code == 200, (role, target, actual.text[:300])
            menu=c.get('/').text
            if role=='student':
                assert 'href="/mess-manager"' in menu and 'href="/compare"' in menu
                assert c.get('/living-cost').status_code==200
                assert c.get('/admin').status_code==403
            if role=='landlord':
                assert 'href="/landlord"' in menu
                for hidden in ('/roommates','/mess-manager','/living-cost','/compare','/fair-rent'):
                    assert 'href="'+hidden+'"' not in menu, hidden
                    assert c.get(hidden).status_code==403,hidden
                assert c.get('/maintenance').status_code==200
                assert c.get('/agreement').status_code==200
            if role=='admin':
                assert 'href="/admin"' in menu
                for hidden in ('/roommates','/mess-manager','/living-cost','/compare','/fair-rent','/maintenance'):
                    assert 'href="'+hidden+'"' not in menu, hidden
                assert c.get('/landlord').status_code==403


def test_missing_smtp_fails_transparently(tmp_path, monkeypatch):
    monkeypatch.setattr(database,'DB_PATH',str(tmp_path/'no_mail.sqlite'))
    monkeypatch.delenv('SMARTRENT_SMTP_HOST',raising=False)
    monkeypatch.delenv('SMARTRENT_SMTP_FROM',raising=False)
    with TestClient(app,follow_redirects=False) as c:
        c.get('/forgot-password')
        csrf=c.cookies.get('smartrent_csrf')
        r=c.post('/forgot-password',data={'email':'any@example.test','csrf_token':csrf})
        assert r.status_code==503
        assert 'not configured' in r.text


def test_templates_styles_and_setup():
    from jinja2 import Environment
    root=Path(__file__).resolve().parents[1]
    for html in (root/'templates').glob('*.html'):
        Environment().parse(html.read_text(encoding='utf-8'))
    detail=(root/'templates/listing_detail.html').read_text(encoding='utf-8')
    css=(root/'static/product.css').read_text(encoding='utf-8')
    assert 'sr-security-notice-icon' in detail and 'grid-template-columns:32px minmax(0,1fr)' in css
    assert 'SmartRent নিরাপত্তা পরামর্শ' in detail
    assert (root/'.env.example').is_file()
    assert 'python-dotenv' in (root/'requirements.txt').read_text(encoding='utf-8')
