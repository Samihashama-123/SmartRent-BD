"""User-bound housing workflows: notifications, verification, booking, mess and comparison.

No external payment provider, automated ID verification, or legal contract issuance.
"""
import calendar
import secrets
from datetime import date, datetime
from urllib.parse import urlsplit

from fastapi import APIRouter, Request, Form, HTTPException
from fastapi.responses import RedirectResponse

from app.auth import SESSION_COOKIE_NAME, get_user_by_session
from app.database import get_db
from app.location_search import search_terms

router = APIRouter(tags=['Core features'])


def account(request, roles=None, write=False):
    user = get_user_by_session(request.cookies.get(SESSION_COOKIE_NAME))
    if not user:
        raise HTTPException(401,'Sign in to continue.')
    if roles and user['role'] not in roles:
        raise HTTPException(403,'Your account cannot perform this action.')
    if write:
        source = request.headers.get('origin') or request.headers.get('referer')
        if not source:
            raise HTTPException(403,'Missing request origin.')
        uri = urlsplit(source)
        if (uri.scheme,uri.netloc)!=(request.url.scheme,request.url.netloc):
            raise HTTPException(403,'Cross-site request refused.')
    return user


def bounded(value, label, low=1, high=255):
    text = str(value or '').strip()
    if not low <= len(text) <= high:
        raise HTTPException(422,f'{label} must contain {low}–{high} characters.')
    return text


def number(value, label, low=0, high=1000000):
    try:
        value = int(value)
    except (ValueError,TypeError,OverflowError):
        raise HTTPException(422,f'Invalid {label}.')
    if not low <= value <= high:
        raise HTTPException(422,f'{label} must be between {low} and {high}.')
    return value


def day(value):
    try:
        return date.fromisoformat(value).isoformat()
    except (ValueError,TypeError):
        raise HTTPException(422,'Provide a valid date.')


def create_search_alerts(conn, listing_id):
    """Only approved, publicly visible properties generate a matching saved-search alert."""
    listing=conn.execute('SELECT * FROM listings WHERE id=? AND is_verified=1 AND is_flagged=0',
                         (listing_id,)).fetchone()
    if not listing:
        return 0
    subscriptions=conn.execute('SELECT * FROM saved_searches').fetchall()
    created=0
    for sub in subscriptions:
        if sub['user_id']==listing['owner_id']:
            continue
        if sub['max_budget'] and listing['rent_amount']>sub['max_budget']:
            continue
        if sub['property_type'] and sub['property_type'] != listing['property_type']:
            continue
        if sub['gender_policy'] and listing['gender_policy'] not in (sub['gender_policy'],'Any'):
            continue
        if sub['university'] and sub['university'].casefold() not in (
            (listing['university_nearby'] or '')+' '+(listing['title'] or '')).casefold():
            continue
        if sub['area']:
            haystack=((listing['area'] or '')+' '+(listing['address'] or '')).casefold()
            if not any(t.casefold() in haystack for t in search_terms(sub['area'])):
                continue
        result=conn.execute('''INSERT OR IGNORE INTO search_alerts
            (user_id,search_id,listing_id) VALUES (?,?,?)''',
            (sub['user_id'],sub['id'],listing_id))
        created+=result.rowcount
    return created


@router.post('/api/admin/verify-checklist')
async def admin_verify_checklist(request:Request,listing_id:int=Form(...),
                                 owner_identity_checked:int=Form(0),
                                 inspection_completed:int=Form(0)):
    account(request,('admin',),write=True)
    if owner_identity_checked not in (0,1) or inspection_completed not in (0,1):
        raise HTTPException(422,'Invalid checklist.')
    with get_db() as conn:
        row=conn.execute('SELECT id FROM listings WHERE id=?',(listing_id,)).fetchone()
        if not row:
            raise HTTPException(404,'Listing not found.')
        conn.execute('''UPDATE listings SET owner_identity_checked=?, inspection_completed=?,
            is_verified=CASE WHEN ?=1 AND ?=1 THEN is_verified ELSE 0 END
            WHERE id=?''', (owner_identity_checked,inspection_completed,
                           owner_identity_checked,inspection_completed,listing_id))
    return {'status':'success','message':'Verification checklist saved; approval requires both checks.'}


@router.post('/api/booking/confirm')
async def booking_confirm(request:Request,visit_id:int=Form(...),decision:str=Form('confirm')):
    user=account(request,('landlord',),write=True)
    if decision not in ('confirm','decline'):
        raise HTTPException(422,'Choose confirm or decline.')
    with get_db() as conn:
        result=conn.execute('''UPDATE visits_and_bookings
            SET status=? WHERE id=? AND owner_id=? AND status='booking_requested'
            AND EXISTS(SELECT 1 FROM listings l WHERE l.id=visits_and_bookings.listing_id
              AND l.owner_id=? AND l.is_flagged=0 AND l.is_verified=1)''',
            ('booked' if decision=='confirm' else 'booking_declined',visit_id,user['id'],user['id']))
        if result.rowcount!=1:
            raise HTTPException(404,'Pending booking request not found.')
    return {'status':'success','message':'Booking confirmed without any real payment.' if decision=='confirm' else 'Booking request declined.'}


@router.get('/compare')
async def compare_page(request:Request):
    user=account(request,('student','landlord'))
    with get_db() as conn:
        rows=[dict(r) for r in conn.execute('''SELECT l.* FROM property_comparisons pc
            JOIN listings l ON l.id=pc.listing_id
            WHERE pc.user_id=? AND l.is_verified=1 AND l.is_flagged=0
            ORDER BY pc.created_at DESC LIMIT 3''',(user['id'],)).fetchall()]
    from main import render
    return render(request,'compare.html',{'current_user':user,'active_nav':'compare','properties':rows})


@router.post('/api/compare/toggle')
async def toggle_compare(request:Request,listing_id:int=Form(...)):
    user=account(request,('student','landlord'),write=True)
    with get_db() as conn:
        match=conn.execute('''SELECT id FROM listings WHERE id=? AND is_verified=1 AND is_flagged=0''',
            (listing_id,)).fetchone()
        if not match: raise HTTPException(404,'Property not available.')
        existing=conn.execute('''SELECT 1 FROM property_comparisons WHERE user_id=? AND listing_id=?''',
            (user['id'],listing_id)).fetchone()
        if existing:
            conn.execute('DELETE FROM property_comparisons WHERE user_id=? AND listing_id=?',(user['id'],listing_id))
            action='removed'
        else:
            total=conn.execute('SELECT COUNT(*) FROM property_comparisons WHERE user_id=?',(user['id'],)).fetchone()[0]
            if total>=3: raise HTTPException(409,'Compare up to three properties. Remove one first.')
            conn.execute('INSERT INTO property_comparisons(user_id,listing_id) VALUES (?,?)',(user['id'],listing_id))
            action='added'
    return {'status':'success','action':action,'message':'Comparison updated.'}


@router.get('/living-cost')
async def living_cost_page(request:Request, listing_id:int=0):
    user=account(request,('student','landlord'))
    selected=None
    if listing_id:
        with get_db() as conn:
            found=conn.execute('SELECT * FROM listings WHERE id=? AND is_verified=1 AND is_flagged=0',(listing_id,)).fetchone()
            if found: selected=dict(found)
    from main import render
    return render(request,'living_cost.html',{'current_user':user,'active_nav':'living_cost','listing':selected})


# Members of a mess control expenses for ONLY their own group.
# A join code is needed to become a member; a student may join one mess at a time.

def membership(conn, user_id):
    return conn.execute('''
        SELECT
            g.*,
            mu.user_id,
            mu.is_manager,
            mu.member_name,
            mu.seat_rent,
            mu.join_code
        FROM mess_memberships mu
        JOIN mess_groups g ON g.id = mu.mess_id
        WHERE mu.user_id = ?
    ''', (user_id,)).fetchone()



async def mess_workspace_page(request:Request):
    user=account(request,('student',))
    chosen=request.query_params.get('month','')
    month=datetime.now().strftime('%Y-%m')
    if chosen:
        if len(chosen) != 7 or chosen[4] != '-' or not chosen[:4].isdigit() or not chosen[5:].isdigit() or not 1 <= int(chosen[5:]) <= 12:
            raise HTTPException(422,'Invalid report month.')
        month=chosen
    with get_db() as conn:
        group=membership(conn,user['id'])
        members=[]; ledger=[]; total_meals=0; total_bazaar=0;total_utility=0;rate=0
        if group:
            gid=group['id']
            members=[dict(r) for r in conn.execute('SELECT * FROM mess_memberships WHERE mess_id=? ORDER BY id',(gid,)).fetchall()]
            ledger=[dict(r) for r in conn.execute('''SELECT e.*,m.member_name FROM mess_expenses e
              JOIN mess_memberships m ON m.user_id=e.user_id AND m.mess_id=e.mess_id
              WHERE e.mess_id=? AND substr(e.entry_date,1,7)=? ORDER BY e.entry_date DESC,e.id DESC''',
              (gid,month)).fetchall()]
            total_bazaar=sum(e['amount'] for e in ledger if e['kind']=='bazaar')
            total_utility=sum(e['amount'] for e in ledger if e['kind']=='utility')
            total_meals=sum(e['amount'] for e in ledger if e['kind']=='meal')
            rate=round(total_bazaar / total_meals,2) if total_meals else 0
            # Values in the monthly ledger are real recorded shares; no seeded totals are mixed in.
            for m in members:
                m['meals']=sum(e['amount'] for e in ledger if e['kind']=='meal' and e['user_id']==m['user_id'])
                m['paid']=sum(e['amount'] for e in ledger if e['kind'] in ('utility','bazaar') and e['user_id']==m['user_id'])
                m['meal_cost']=round(m['meals']*rate,2)
                m['utility_share']=round(total_utility/len(members),2)
                m['total_cost']=round(m['meal_cost']+m['utility_share']+m['seat_rent'],2)
                m['balance']=round(m['paid']-m['meal_cost']-m['utility_share'],2)
    from main import render
    return render(request,'mess_workspace.html',{'current_user':user,'active_nav':'mess',
        'mess':dict(group) if group else None,'members':members,'ledger':ledger,'month':month,
        'total_meals':total_meals,'total_bazaar':total_bazaar,'total_utility':total_utility,
        'meal_rate':rate,'today':date.today().isoformat()})


@router.post('/api/mess/create')
async def mess_create(request:Request,name:str=Form(...),address:str=Form(...),
                      seat_rent:int=Form(0)):
    user=account(request,('student',),write=True)
    name=bounded(name,'Mess name',3,100)
    address=bounded(address,'Address',3,180)
    seat_rent=number(seat_rent,'Seat rent',0,100000)
    join_code=secrets.token_urlsafe(9)
    with get_db() as conn:
        if membership(conn,user['id']):raise HTTPException(409,'Already a member of a mess.')
        row=conn.execute('''INSERT INTO mess_groups(name,address,monthly_rent) VALUES (?,?,0)''',(name,address))
        conn.execute('''INSERT INTO mess_memberships(mess_id,user_id,is_manager,member_name,seat_rent,join_code)
        VALUES (?,?,1,?,?,?)''',(row.lastrowid,user['id'],user['name'],seat_rent,join_code))
    return {'status':'success','message':'Mess created. Share the join code only with roommates.'}


@router.post('/api/mess/join')
async def mess_join(request:Request,join_code:str=Form(...),seat_rent:int=Form(0)):
    user=account(request,('student',),write=True)
    seat_rent=number(seat_rent,'Seat rent',0,100000)
    with get_db() as conn:
        if membership(conn,user['id']):raise HTTPException(409,'Already a member of a mess.')
        manager=conn.execute('SELECT mess_id FROM mess_memberships WHERE join_code=? AND is_manager=1',(join_code.strip(),)).fetchone()
        if not manager:raise HTTPException(404,'Invalid mess join code.')
        conn.execute('''INSERT INTO mess_memberships(mess_id,user_id,is_manager,member_name,seat_rent)
            VALUES (?,?,0,?,?)''',(manager['mess_id'],user['id'],user['name'],seat_rent))
    return {'status':'success','message':'Joined mess successfully.'}


@router.post('/api/mess/record')
async def mess_record(request:Request,kind:str=Form(...),amount:int=Form(...),
                      entry_date:str=Form(...),memo:str=Form('')):
    user=account(request,('student',),write=True)
    if kind not in ('bazaar','utility','meal'):raise HTTPException(422,'Invalid record type.')
    amount=number(amount,'Amount',0 if kind=='meal' else 1, 100000)
    memo=bounded(memo,'Description',0,180)
    entry_date=day(entry_date)
    with get_db() as conn:
        group=membership(conn,user['id'])
        if not group:raise HTTPException(403,'Join or create a mess first.')
        conn.execute('''INSERT INTO mess_expenses(mess_id,user_id,kind,amount,entry_date,memo)
            VALUES (?,?,?,?,?,?)''',(group['id'],user['id'],kind,amount,entry_date,memo))
    return {'status':'success','message':'Mess record saved.'}


@router.post('/api/mess/seat-rent')
async def mess_seat_rent(request:Request,seat_rent:int=Form(...)):
    user=account(request,('student',),write=True)
    seat_rent=number(seat_rent,'Seat rent',0,100000)
    with get_db() as conn:
        result=conn.execute('UPDATE mess_memberships SET seat_rent=? WHERE user_id=?',(seat_rent,user['id']))
        if result.rowcount!=1: raise HTTPException(404,'Join a mess first.')
    return {'status':'success','message':'Rent saved.'}


@router.post('/api/mess/leave')
async def mess_leave(request:Request):
    user=account(request,('student',),write=True)
    with get_db() as conn:
        group=membership(conn,user['id'])
        if not group:raise HTTPException(404,'No mess membership.')
        if group['is_manager']:
            others=conn.execute('SELECT COUNT(*) FROM mess_memberships WHERE mess_id=? AND user_id!=?',
                (group['id'],user['id'])).fetchone()[0]
            if others:raise HTTPException(409,'Manager must remove or transfer group members before leaving.')
        historical=conn.execute('SELECT COUNT(*) FROM mess_expenses WHERE mess_id=? AND user_id=?',
            (group['id'],user['id'])).fetchone()[0]
        if historical:
            raise HTTPException(409,'Cannot leave a mess with historical ledger records; retain the member for an auditable monthly summary.')
        conn.execute('DELETE FROM mess_memberships WHERE user_id=?',(user['id'],))
    return {'status':'success','message':'Left mess. Historical ledger preserved.'}
