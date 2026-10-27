"""v9 UI regression checks, isolated from the real user database."""
from datetime import date, timedelta
from fastapi.testclient import TestClient
from app import database, auth
from main import app


def test_v9_custom_university_and_role_based_maintenance(tmp_path, monkeypatch):
    monkeypatch.setattr(database, 'DB_PATH', str(tmp_path / 'v9.sqlite'))
    database.init_db()
    owner=auth.register_user('Owner', 'owner-v9@example.test', '01700000051', 'secure-test-password', role='landlord')
    student=auth.register_user('Student', 'student-v9@example.test', '01700000052', 'secure-test-password', role='student')
    with database.get_db() as conn:
        conn.execute("""INSERT INTO listings
        (owner_id,title,description,property_type,address,area,university_nearby,
        distance_km,rent_amount,deposit_amount,gender_policy,availability_date,photos,lat,lng,
        facilities,is_verified,is_flagged)
        VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,1,0)""",
        (owner['id'], 'Quiet room close to a new college', 'A test accommodation for students',
         'Single Room','Matidali, Bogura','Matidali','Bogura Government College',
         1.2,4200,1000,'Any',(date.today()+timedelta(days=5)).isoformat(),'[]',
         24.88,89.37,'["wifi"]'))
        listing_id=conn.execute('SELECT last_insert_rowid()').fetchone()[0]
    with TestClient(app,follow_redirects=False) as c:
        # Public user can type an arbitrary university name via datalist input.
        page=c.get('/listings',follow_redirects=False)
        assert page.status_code==200
        assert 'id="srUniversityPreset"' in page.text
        assert 'id="universitySearch" name="university" type="text"' in page.text
        assert 'class="sr-listing-view-cta ' in page.text
        r=c.get('/listings?university=Bogura+Government+College',follow_redirects=False)
        assert r.status_code==200 and 'Quiet room close' in r.text
        assert 'Quiet room close' not in c.get('/listings?university=Unknown+University').text
        # Landlord can manage but must never see student-only ticket submission.
        c.cookies.set(auth.SESSION_COOKIE_NAME, auth.create_session(owner['id']))
        landlord=c.get('/maintenance',follow_redirects=False)
        assert landlord.status_code==200
        assert 'Landlord maintenance workspace' in landlord.text
        assert 'id="ticketModal"' not in landlord.text
        assert 'onclick="openTicketModal()"' not in landlord.text
        assert 'src="/static/' in c.get('/landlord').text
        owner_page=c.get('/landlord').text
        assert 'id="propertyPhotoFiles"' in owner_page
        assert 'sr-photo-file-input' in owner_page
        assert 'sr-photo-action' in owner_page
        # A student without booked rental must see guidance, not an unusable form.
        c.cookies.set(auth.SESSION_COOKIE_NAME, auth.create_session(student['id']))
        empty=c.get('/maintenance').text
        assert 'no confirmed bookings' in empty
        assert 'id="ticketModal"' not in empty
        # Once landlord-confirmed booking exists, only that home appears.
        with database.get_db() as conn:
            conn.execute("""INSERT INTO visits_and_bookings
            (listing_id,student_id,owner_id,visit_date,time_slot,status)
            VALUES(?,?,?,?,?,?)""",
            (listing_id,student['id'],owner['id'],date.today().isoformat(),'Morning','booked'))
        filled=c.get('/maintenance').text
        assert 'id="ticketModal"' in filled
        assert 'id="maintenance-listing"' in filled
        assert 'Quiet room close to a new college' in filled
        assert 'id="srCustomCategory"' in filled
        # The backend already accepts validated custom categories; JS maps Other to category.
        sent=c.post('/api/submit-maintenance',data={
            'tenant_id':student['id'],'owner_id':owner['id'],'listing_id':listing_id,
            'category':'Roof leakage','title':'Water dripping from the ceiling',
            'description':'Water drips from the ceiling during rain.', 'priority':'medium',
        },headers={'Origin':'http://testserver'})
        assert sent.status_code==200,sent.text
        with database.get_db() as conn:
            saved=conn.execute('SELECT category,title FROM maintenance_requests WHERE listing_id=?',
                               (listing_id,)).fetchone()
        assert saved['category']=='Roof leakage'
        ticket_id=conn.execute('SELECT id FROM maintenance_requests WHERE listing_id=?', (listing_id,)).fetchone()[0]
        # Student cannot change ticket status; owner cannot skip the acceptance step.
        attempt=c.post('/api/landlord/maintenance-status',data={'ticket_id':ticket_id,'status':'resolved'},headers={'Origin':'http://testserver'})
        assert attempt.status_code==403
        c.cookies.set(auth.SESSION_COOKIE_NAME, auth.create_session(owner['id']))
        attempt=c.post('/api/landlord/maintenance-status',data={'ticket_id':ticket_id,'status':'resolved'},headers={'Origin':'http://testserver'})
        assert attempt.status_code==404
        accepted=c.post('/api/landlord/maintenance-status',data={'ticket_id':ticket_id,'status':'in_progress'},headers={'Origin':'http://testserver'})
        assert accepted.status_code==200,accepted.text
        resolved=c.post('/api/landlord/maintenance-status',data={'ticket_id':ticket_id,'status':'resolved'},headers={'Origin':'http://testserver'})
        assert resolved.status_code==200,resolved.text
        repeat=c.post('/api/landlord/maintenance-status',data={'ticket_id':ticket_id,'status':'resolved'},headers={'Origin':'http://testserver'})
        assert repeat.status_code==404
        with database.get_db() as conn:
            final=conn.execute('SELECT status,resolved_at FROM maintenance_requests WHERE id=?',(ticket_id,)).fetchone()
        assert final['status']=='resolved' and final['resolved_at']
