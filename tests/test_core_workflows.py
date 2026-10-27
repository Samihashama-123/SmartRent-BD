"""Test real SmartRent role and workflow invariants with a new disposable SQLite DB.

Run: python -m pytest -q tests
This NEVER reads or alters the user's existing smartrent.db data.
"""
import sys
from datetime import date, timedelta
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import app.database as database
from app.auth import hash_password, create_session
from main import app

ORIGIN = "http://testserver"


@pytest.fixture()
def environment(tmp_path, monkeypatch):
    monkeypatch.setattr(database, "DB_PATH", str(tmp_path / "unit.db"))
    database.init_db()
    with database.get_db() as conn:
        for name, role in [("New Student", "student"), ("Property Owner", "landlord"),
                           ("Review Admin", "admin"), ("Second Student", "student")]:
            conn.execute("""INSERT INTO users(name,email,phone,role,password_hash)
                VALUES(?,?,?,?,?)""",
                (name, name.lower().replace(' ', '.') + '@example.test',
                 '01900000000', role, hash_password('TestingOnlyPassword!1')))
    with TestClient(app) as client:
        yield client


def signed(client,uid):
    client.cookies.set("smartrent_session",create_session(uid))


def post(client,path,**data):
    return client.post(path,data=data,headers={'Origin':ORIGIN})


def new_listing(client):
    signed(client,2)
    fields = dict(title='Bogura verified student room', description='Furnished room with Wi-Fi',
        title_bn='বগুড়ায় শিক্ষার্থীদের কক্ষ',description_bn='ওয়াই-ফাইসহ সজ্জিত কক্ষ',
        property_type='Single Room',area='Matidali',university_nearby='PUST',
        distance_km='1.0',rent_amount='5000',deposit_amount='1000',
        address='Matidali, Bogura, Bangladesh',gender_policy='Any',
        availability_date=(date.today()+timedelta(days=4)).isoformat(),
        lat='24.883',lng='89.373',photo_url='https://example.com/room.jpg',
        additional_photo_urls='https://example.com/kitchen.jpg',fac_wifi='on')
    r=post(client,'/api/landlord/create',**fields)
    assert r.status_code==200,r.text
    return r.json()['listing_id']


def approve(client,listing_id):
    signed(client,3)
    r=post(client,'/api/admin-toggle-verify',listing_id=listing_id,is_verified=1)
    assert r.status_code==409
    r=post(client,'/api/admin/verify-checklist',listing_id=listing_id,owner_identity_checked=1,inspection_completed=1)
    assert r.status_code==200,r.text
    r=post(client,'/api/admin-toggle-verify',listing_id=listing_id,is_verified=1)
    assert r.status_code==200,r.text


def test_language_and_scoped_pages(environment):
    c=environment
    signed(c,1)
    for language,expected in [('bn','বাসা খুঁজুন'),('en','Find Housing')]:
        c.cookies.set('smartrent_lang',language)
        for path in ('/','/listings','/roommates','/agreement','/profile','/living-cost','/compare','/mess-manager','/my-bookings'):
            r=c.get(path,follow_redirects=False)
            assert r.status_code==200,(path,r.text[:250])
            if path == '/my-bookings': assert ('ভিজিট' if language=='bn' else 'visits') in r.text
        assert expected in c.get('/listings').text
    assert c.get('/admin',follow_redirects=False).status_code==403
    assert c.get('/landlord',follow_redirects=False).status_code==403


def test_search_approval_report_visibility_and_reviews(environment):
    c=environment
    signed(c,1)
    assert post(c,'/api/save-search',user_id=999,area='Bogura',max_budget=6000).status_code==200
    listing=new_listing(c)
    signed(c,1)
    assert post(c,'/api/submit-review',listing_id=listing,student_id=1,rating=4,comment='Very nice home').status_code==404
    approve(c,listing)
    signed(c,1)
    with database.get_db() as conn:
        assert conn.execute('SELECT count(*) FROM search_alerts WHERE user_id=1 AND listing_id=?',(listing,)).fetchone()[0]==1
    page=c.get('/listings?area=Bogura').text
    assert 'Bogura verified student room' in page
    c.cookies.set('smartrent_lang','bn')
    assert 'বগুড়ায় শিক্ষার্থীদের কক্ষ' in c.get('/listings?area=Bogura').text
    assert post(c,'/api/submit-review',listing_id=listing,student_id=1,rating=4,comment='Very nice home').status_code==403
    assert post(c,'/api/simulated-booking',listing_id=listing).status_code==409
    r=post(c,'/api/request-visit',listing_id=listing,student_id=2,owner_id=2,
           visit_date=(date.today()+timedelta(days=5)).isoformat(),time_slot='Morning')
    assert r.status_code==200,r.text
    with database.get_db() as conn:
        visit=conn.execute('SELECT * FROM visits_and_bookings WHERE listing_id=?',(listing,)).fetchone()
        assert (visit['student_id'],visit['owner_id'])==(1,2)
        vid=visit['id']
    page = c.get('/my-bookings').text
    assert 'Bogura verified student room' in page
    assert 'Visit pending' in page or 'ভিজিট অপেক্ষমাণ' in page
    signed(c,2)
    assert post(c,'/api/landlord/visit-status',visit_id=vid,
                visit_date=(date.today()+timedelta(days=6)).isoformat(),
                time_slot='Evening (5:00 PM - 8:00 PM)').status_code==200
    signed(c,1)
    assert post(c,'/api/simulated-booking',listing_id=listing,student_id=999,owner_id=999,visit_id=vid).status_code==200
    assert 'Booking pending' in c.get('/my-bookings').text or 'বুকিং অপেক্ষমাণ' in c.get('/my-bookings').text
    with database.get_db() as conn:
        assert conn.execute('SELECT status FROM visits_and_bookings WHERE id=?',(vid,)).fetchone()[0]=='booking_requested'
    signed(c,2)
    assert post(c,'/api/booking/confirm',visit_id=vid,decision='confirm').status_code==200
    signed(c,1)
    assert 'Booked' in c.get('/my-bookings').text or 'বুকিং নিশ্চিত' in c.get('/my-bookings').text
    assert post(c,'/api/submit-review',listing_id=listing,student_id=999,rating=5,comment='Stayed, was comfortable').status_code==200
    assert post(c,'/api/submit-review',listing_id=listing,student_id=999,rating=5,comment='Duplicate').status_code==409
    assert post(c,'/api/submit-maintenance',listing_id=listing,tenant_id=999,owner_id=999,
                category='electrical',title='Light is not working',
                description='Need to check the room lighting').status_code==200
    r=post(c,'/api/report-listing',listing_id=listing,reporter_id=999,
           reason='Suspicious claim',details='Potentially false owner claim')
    assert r.status_code==200,r.text
    assert 'Bogura verified student room' not in c.get('/listings?area=Bogura').text
    with database.get_db() as conn:
        rid=conn.execute('SELECT id FROM reports WHERE listing_id=?',(listing,)).fetchone()[0]
    signed(c,3)
    assert post(c,'/api/admin-report-action',report_id=rid,listing_id=listing,action='dismiss').status_code==200
    signed(c,1)
    c.cookies.set('smartrent_lang','en')
    assert 'Bogura verified student room' in c.get('/listings?area=Bogura').text
    # tenant data cannot be forged to grant unrelated student reviews
    signed(c,4)
    assert post(c,'/api/submit-review',listing_id=listing,student_id=1,rating=5,comment='Fraudulent review').status_code==403


def test_compare_and_private_mess(environment):
    c=environment
    listing=new_listing(c);approve(c,listing)
    signed(c,1)
    assert post(c,'/api/compare/toggle',listing_id=listing).status_code==200
    assert 'Bogura verified student room' in c.get('/compare').text
    assert c.get('/living-cost?listing_id='+str(listing)).status_code==200
    assert post(c,'/api/mess/create',name='Matidali Student Mess',address='Bogura City',seat_rent=3200).status_code==200
    with database.get_db() as conn:
        joincode=conn.execute('SELECT join_code FROM mess_memberships WHERE user_id=1').fetchone()[0]
    assert post(c,'/api/mess/record',kind='bazaar',amount=2000,
                entry_date=date.today().isoformat(),memo='Monthly groceries').status_code==200
    assert post(c,'/api/mess/record',kind='meal',amount=10,
                entry_date=date.today().isoformat(),memo='Meal count').status_code==200
    assert 'Matidali Student Mess' in c.get('/mess-manager').text
    signed(c,4)
    assert 'Matidali Student Mess' not in c.get('/mess-manager').text
    assert post(c,'/api/mess/join',join_code=joincode,seat_rent=3000).status_code==200
    assert 'Matidali Student Mess' in c.get('/mess-manager').text
    signed(c,2)
    assert post(c,'/api/mess/record',kind='bazaar',amount=12,entry_date=date.today().isoformat()).status_code==403


def test_booking_navigation_and_maintenance_empty_state(environment):
    c=environment
    signed(c,1)
    c.cookies.set('smartrent_lang','bn')
    housing=c.get('/listings').text
    assert 'কীভাবে বুক করবেন' in housing
    assert 'id="sr-smart-back"' in housing
    assert 'href="/my-bookings"' in housing
    maintenance=c.get('/maintenance').text
    assert 'আপনার এখনো কোনো নিশ্চিত বুকিং নেই' in maintenance
    assert 'href="/my-bookings"' in maintenance
    planner=c.get('/living-cost').text
    assert 'data-currency="BDT"' in planner
    listing=new_listing(c)
    approve(c,listing)
    signed(c,1)
    detail=c.get('/listings/'+str(listing)).text
    assert 'বাসা বুকিং করার নিয়ম' in detail
    assert 'ভিজিটের অনুরোধ পাঠান' in detail
    assert 'href="/my-bookings"' in detail
