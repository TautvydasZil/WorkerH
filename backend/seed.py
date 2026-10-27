import sys
from datetime import date, datetime, timedelta
from sqlalchemy import text

from extensions import db
from models import User, Project, Task, HoursLogged, LeaveRequest, Invite


def ensure_schema():
    db.create_all()
    try:
        cols = [row[1] for row in db.session.execute(text('PRAGMA table_info(hours_logged)')).fetchall()]
        if 'task_id' not in cols:
            db.session.execute(text('ALTER TABLE hours_logged ADD COLUMN task_id INTEGER REFERENCES task(id)'))
            db.session.commit()
    except Exception:
        db.session.rollback()


def seed_database(reset=False):
    ensure_schema()

    if reset:
        HoursLogged.query.delete()
        LeaveRequest.query.delete()
        Task.query.delete()
        Project.query.delete()
        Invite.query.delete()
        User.query.delete()
        db.session.commit()

    if (
        User.query.count() >= 5
        and Project.query.count() >= 5
        and Task.query.count() >= 5
        and HoursLogged.query.count() >= 5
    ):
        return False

    # Jei trūksta įrašų iki >= 5 kiekvienoje lentelėje, perpilame švariai
    HoursLogged.query.delete()
    LeaveRequest.query.delete()
    Task.query.delete()
    Project.query.delete()
    Invite.query.delete()
    db.session.commit()

    # 1. Naudotojai (5 įrašai)
    def get_or_create_user(username, email, first_name, last_name, role, pw):
        u = User.query.filter_by(username=username).first()
        if not u:
            u = User(
                username=username,
                email=email,
                first_name=first_name,
                last_name=last_name,
                role=role,
                is_active=True
            )
            u.set_password(pw)
            db.session.add(u)
        return u

    admin   = get_or_create_user('admin', 'admin@workerh.lt', 'Tautvydas', 'Žilinskas', 'admin', 'admin123')
    manager = get_or_create_user('vadybininkas', 'tomas@workerh.lt', 'Tomas', 'Vaitkus', 'manager', 'vadyba123')
    w1      = get_or_create_user('jonas', 'jonas@workerh.lt', 'Jonas', 'Kazlauskas', 'worker', 'darbas123')
    w2      = get_or_create_user('petras', 'petras@workerh.lt', 'Petras', 'Petrauskas', 'worker', 'darbas123')
    w3      = get_or_create_user('asta', 'asta@workerh.lt', 'Asta', 'Jankauskienė', 'worker', 'darbas123')
    db.session.flush()

    # 2. Projektai (Project - 1 lygmuo: 6 prasmingi įrašai, >= 5)
    p1 = Project(
        name='Verslo centro „Kauno Dokas“ renovacija',
        address='Jonavos g. 7, Kaunas',
        latitude=54.9027,
        longitude=23.8863,
        is_completed=False
    )
    p2 = Project(
        name='Saulės elektrinės montavimas Klaipėdoje',
        address='Pramonės g. 15, Klaipėda',
        latitude=55.6894,
        longitude=21.1793,
        is_completed=False
    )
    p3 = Project(
        name='Logistikos sandėlio elektros instaliacija',
        address='Savanorių pr. 174, Vilnius',
        latitude=54.6512,
        longitude=25.2219,
        is_completed=False
    )
    p4 = Project(
        name='KTU Studentų miestelio apšvietimo atnaujinimas',
        address='Studentų g. 48, Kaunas',
        latitude=54.9041,
        longitude=23.9576,
        is_completed=False
    )
    p5 = Project(
        name='Gamybinio cecho automatikos diegimas Panevėžyje',
        address='J. Janonio g. 30, Panevėžys',
        latitude=55.7348,
        longitude=24.3275,
        is_completed=False
    )
    p6 = Project(
        name='Daugiabučio šildymo punkto modernizavimas',
        address='K. Donelaičio g. 60, Kaunas',
        latitude=54.8992,
        longitude=23.9135,
        is_completed=True
    )
    db.session.add_all([p1, p2, p3, p4, p5, p6])
    db.session.flush()

    # 3. Užduotys (Task - 2 lygmuo: 12 prasmingų įrašų, >= 5)
    t1 = Task(
        project_id=p1.id,
        title='Elektros instaliacijos paruošimas',
        description='Kabelių vedžiojimas 2 aukšte ir paskirstymo dėžučių montavimas',
        status='in_progress'
    )
    t2 = Task(
        project_id=p1.id,
        title='LED šviestuvų ir jutiklių montavimas',
        description='Konferencijų salių ir darbo erdvių apšvietimo įrengimas',
        status='todo'
    )
    t3 = Task(
        project_id=p1.id,
        title='Priešgaisrinės signalizacijos patikra',
        description='Dūmų detektorių ir centralės testavimas',
        status='done'
    )
    t4 = Task(
        project_id=p2.id,
        title='Laikančiųjų konstrukcijų montavimas ant stogo',
        description='Aliuminio profilių tvirtinimas prie stogo dangos',
        status='done'
    )
    t5 = Task(
        project_id=p2.id,
        title='Saulės modulių ir inverterių pajungimas',
        description='50 kW saulės elektrinės modulių sujungimas į grandines',
        status='in_progress'
    )
    t6 = Task(
        project_id=p2.id,
        title='Sistemos testavimas ir pridavimas ESO',
        description='Izoliacijos varžų matavimai ir dokumentacijos paruošimas',
        status='todo'
    )
    t7 = Task(
        project_id=p3.id,
        title='Paskirstymo skydų surinkimas',
        description='Pagrindinio įvadinio skydo ir automatikos montavimas',
        status='in_progress'
    )
    t8 = Task(
        project_id=p3.id,
        title='Pramoninio apšvietimo linijų vedžiojimas',
        description='Aukštuminių šviestuvų kabelių trasų montavimas',
        status='todo'
    )
    t9 = Task(
        project_id=p4.id,
        title='Lauko apšvietimo atramų kabeliavimas',
        description='Požeminių kabelių klojimas ir atramų įžeminimo matavimai',
        status='in_progress'
    )
    t10 = Task(
        project_id=p4.id,
        title='Išmaniųjų šviesos srauto valdiklių programavimas',
        description='DALI valdiklių adresavimas ir pritemdymo grafikų nustatymas',
        status='todo'
    )
    t11 = Task(
        project_id=p5.id,
        title='PLC valdiklių spintos surinkimas',
        description='Pramoninių valdiklių ir dažnio keitiklių montavimas',
        status='in_progress'
    )
    t12 = Task(
        project_id=p6.id,
        title='Šilumokaičio automatikos pajungimas',
        description='Temperatūros jutiklių ir valdiklio konfigūravimas',
        status='done'
    )
    db.session.add_all([t1, t2, t3, t4, t5, t6, t7, t8, t9, t10, t11, t12])
    db.session.flush()

    # 4. Darbo laiko įrašai (HoursLogged / WorkHours - 3 lygmuo: 9 prasmingi įrašai, >= 5)
    today = date.today()
    hours_entries = [
        HoursLogged(
            user_id=w1.id, project_id=p1.id, task_id=t1.id,
            date=today - timedelta(days=6), start_time='08:00', end_time='17:00',
            lunch_break=60, hours=8.0,
            notes='Išvedžioti pagrindiniai maitinimo kabeliai rytiniame korpuse'
        ),
        HoursLogged(
            user_id=w1.id, project_id=p1.id, task_id=t1.id,
            date=today - timedelta(days=5), start_time='08:00', end_time='16:30',
            lunch_break=30, hours=8.0,
            notes='Sumontuotos 14 paskirstymo dėžučių ir atliktas žymėjimas'
        ),
        HoursLogged(
            user_id=w1.id, project_id=p1.id, task_id=t3.id,
            date=today - timedelta(days=4), start_time='08:30', end_time='17:00',
            lunch_break=30, hours=8.0,
            notes='Patikrinti 24 dūmų jutikliai ir sukalibruota centralė'
        ),
        HoursLogged(
            user_id=w1.id, project_id=p4.id, task_id=t9.id,
            date=today - timedelta(days=3), start_time='08:00', end_time='17:00',
            lunch_break=60, hours=8.0,
            notes='Pakloti 120 m požeminio kabelio tarp 1 ir 4 atramų'
        ),
        HoursLogged(
            user_id=w2.id, project_id=p2.id, task_id=t4.id,
            date=today - timedelta(days=5), start_time='07:30', end_time='16:30',
            lunch_break=60, hours=8.0,
            notes='Sumontuoti aliuminio bėgeliai A ir B sektoriuose'
        ),
        HoursLogged(
            user_id=w2.id, project_id=p2.id, task_id=t5.id,
            date=today - timedelta(days=3), start_time='08:00', end_time='17:00',
            lunch_break=60, hours=8.0,
            notes='Sukelti ir pritvirtinti 40 saulės modulių, prijungtas 1 inverteris'
        ),
        HoursLogged(
            user_id=w2.id, project_id=p5.id, task_id=t11.id,
            date=today - timedelta(days=2), start_time='08:00', end_time='16:30',
            lunch_break=30, hours=8.0,
            notes='Sumontuoti Siemens PLC moduliai ir sujungtos valdymo relės'
        ),
        HoursLogged(
            user_id=w3.id, project_id=p3.id, task_id=t7.id,
            date=today - timedelta(days=3), start_time='08:00', end_time='16:00',
            lunch_break=30, hours=7.5,
            notes='Surinktas pagrindinis automatikos skydas pagal schemą'
        ),
        HoursLogged(
            user_id=w3.id, project_id=p1.id, task_id=t2.id,
            date=today - timedelta(days=1), start_time='09:00', end_time='17:30',
            lunch_break=30, hours=8.0,
            notes='Sumontuoti LED paneliai didžiojoje konferencijų salėje'
        ),
    ]
    db.session.add_all(hours_entries)

    # 5. Atostogų ir nedarbingumo prašymai (LeaveRequest: 5 įrašai)
    leave_entries = [
        LeaveRequest(
            user_id=w1.id, type='vacation',
            start_date=today + timedelta(days=10), end_date=today + timedelta(days=14),
            notes='Kasmetinės rudens atostogos', status='pending'
        ),
        LeaveRequest(
            user_id=w2.id, type='sick',
            start_date=today - timedelta(days=12), end_date=today - timedelta(days=10),
            notes='Peršalimas, nedarbingumo pažymėjimas', status='approved',
            reviewed_by=manager.id, reviewed_at=datetime.utcnow() - timedelta(days=12)
        ),
        LeaveRequest(
            user_id=w3.id, type='vacation',
            start_date=today + timedelta(days=20), end_date=today + timedelta(days=22),
            notes='Šeimos šventė', status='approved',
            reviewed_by=manager.id, reviewed_at=datetime.utcnow() - timedelta(days=1)
        ),
        LeaveRequest(
            user_id=w1.id, type='vacation',
            start_date=today - timedelta(days=30), end_date=today - timedelta(days=26),
            notes='Poilsinė kelionė', status='approved',
            reviewed_by=manager.id, reviewed_at=datetime.utcnow() - timedelta(days=35)
        ),
        LeaveRequest(
            user_id=w2.id, type='vacation',
            start_date=today + timedelta(days=30), end_date=today + timedelta(days=32),
            notes='Asmeniniai reikalai', status='pending'
        ),
    ]
    db.session.add_all(leave_entries)

    # 6. Pakvietimai (Invite)
    inv = Invite(
        token='demo-invite-token-workerh-2026',
        email='naujas.darbuotojas@workerh.lt',
        role='worker',
        used=False,
        expires_at=datetime.utcnow() + timedelta(days=7)
    )
    db.session.add(inv)

    db.session.commit()
    return True


if __name__ == '__main__':
    from app import app
    reset_flag = '--reset' in sys.argv
    with app.app_context():
        seeded = seed_database(reset=reset_flag)
        if seeded:
            print('Duomenu baze sekmingai uzpildyta prasmingais duomenimis (>= 5 irasai kiekvienoje lenteleje)!')
        else:
            print('Duomenu baze jau turi >= 5 irasus kiekvienoje lenteleje.')
