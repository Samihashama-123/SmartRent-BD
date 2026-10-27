"""Authenticated photo upload tests using a disposable database."""
import io
from pathlib import Path
from fastapi.testclient import TestClient
from PIL import Image
from app import database, auth
from main import app


def test_landlord_upload_and_listing(tmp_path, monkeypatch):
    monkeypatch.setattr(database, 'DB_PATH', str(tmp_path/'upload.sqlite'))
    import app.landlord_routes as routes
    monkeypatch.setattr(routes,'PHOTO_ROOT', tmp_path/'static/uploads/users')
    database.init_db()
    owner=auth.register_user('Test Landlord','newowner@sample.org','01722223333','password-test-24',role='landlord')
    student=auth.register_user('Test Student','newstudent@sample.org','01722223334','password-test-24',role='student')
    image=Image.new('RGB',(360,240),(30,110,80))
    contents=io.BytesIO();image.save(contents,'PNG')
    def upload(c,contents,content_type):
        return c.post('/api/landlord/photos/upload',files={'file':('room.png',contents,content_type)},headers={'Origin':'http://testserver'})
    with TestClient(app) as c:
        assert upload(c,b'not an image','image/png').status_code==401
        c.cookies.set(auth.SESSION_COOKIE_NAME,auth.create_session(student['id']))
        assert upload(c,contents.getvalue(),'image/png').status_code==403
        c.cookies.set(auth.SESSION_COOKIE_NAME,auth.create_session(owner['id']))
        assert c.post('/api/landlord/photos/upload',files={'file':('x.png',contents.getvalue(),'image/png')}).status_code==403
        assert upload(c,b'not an image','image/png').status_code==422
        good=upload(c,contents.getvalue(),'image/png')
        assert good.status_code==200,good.text
        url=good.json()['url']
        assert url.startswith('/static/uploads/users/'+str(owner['id'])+'/')
        # Upload is stored as a genuinely decoded JPEG, not arbitrary file contents.
        photo=(tmp_path / 'static/uploads/users' / str(owner['id']) / url.rsplit('/',1)[-1])
        assert photo.read_bytes().startswith(b'\xff\xd8')
        assert upload(c,b'garbage','image/png').status_code==422
        assert routes._validated_image_url(url,owner['id'])==url
        # Uploaded local path must be accepted by the real listing creation API.
        from datetime import date, timedelta
        values=dict(title='Bogura room uploaded photo',
             title_bn='বগুড়ার একটি রুম',description='Photo uploaded by property owner',
             description_bn='মালিকের আপলোড করা ছবি',
             property_type='Single Room',area='Matidali',
             address='Matidali, Bogura',university_nearby='Pundra University',
             distance_km='1',rent_amount='5000',deposit_amount='1000',
             gender_policy='Any',availability_date=(date.today()+timedelta(days=5)).isoformat(),
             lat='24.87',lng='89.35',photo_url=url,
             additional_photo_urls='')
        created=c.post('/api/landlord/create',data=values,headers={'Origin':'http://testserver'})
        assert created.status_code==200,created.text
        with database.get_db() as conn:
             saved=conn.execute('SELECT photos,is_verified FROM listings WHERE id=?',
                                (created.json()['listing_id'],)).fetchone()
        assert url in saved['photos'] and saved['is_verified']==0
        from fastapi import HTTPException
        try:
            routes._validated_image_url(url,student['id'])
        except HTTPException as error:
            assert error.status_code==422
        else:
            raise AssertionError('Cross-account image reference was permitted')
