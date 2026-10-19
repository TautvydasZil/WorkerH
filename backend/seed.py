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

    if User.query.first() is not None and Project.query.first() is not None and Task.query.first() is not None:
        return False

    # 1. Naudotojai (Users)
    admin = User.query.filter_by(username='admin').first()
    if not admin:
        admin = User(
            username='admin',
            email='admin@workerh.lt',
            first_name='Tautvydas',
            last_name='Žilinskas',
            role='admin',
            is_active=True
        )
        admin.set_password('admin123')
        db.session.add(admin)

    manager = User.query.filter_by(username='vadybininkas').first()
    if not manager:
        manager = User(
            username='vadybininkas',
            email='tomas@workerh.lt',
            first_name='Tomas',
            last_name='Vaitkus',
            role='manager',
            is_active=True
        )
        manager.set_password('vadyba123')
        db.session.add(manager)

    w1 = User.query.filter_by(username='jonas').first()
    if not w1:
        w1 = User(
            username='jonas',
            email='jonas@workerh.lt',
            first_name='Jonas',
            last_name='Kazlauskas',
            role='worker',
            is_active=True
        )
        w1.set_password('darbas123')
        db.session.add(w1)

    w2 = User.query.filter_by(username='petras').first()
    if not w2:
        w2 = User(
            username='petras',
            email='petras@workerh.lt',
            first_name='Petras',
            last_name='Petrauskas',
            role='worker',
            is_active=True
        )
        w2.set_password('darbas123')
        db.session.add(w2)

    w3 = User.query.filter_by(username='asta').first()
    if not w3:
        w3 = User(
            username='asta',
            email='asta@workerh.lt',
            first_name='Asta',
            last_name='Jankauskienė',
            role='worker',
            is_active=True
        )
        w3.set_password('darbas123')
        db.session.add(w3)

    db.session.flush()

    # 2. Projektai (Projects - 1 lygmuo)
    if Project.query.count() == 0:
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
            name='Daugiabučio šildymo punkto modernizavimas',
            address='K. Donelaičio g. 60, Kaunas',
            latitude=54.8992,
            longitude=23.9135,
            is_completed=True
        )
        db.session.add_all([p1, p2, p3, p4])
        db.session.flush()
    else:
        projects = Project.query.order_by(Project.id).all()
        p1 = projects[0]
        p2 = projects[1] if len(projects) > 1 else p1
        p3 = projects[2] if len(projects) > 2 else p1
        p4 = projects[3] if len(projects) > 3 else p1

    # 3. Užduotys (Tasks - 2 lygmuo)
    if Task.query.count() == 0:
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
            title='Šilumokaičio automatikos pajungimas',
            description='Temperatūros jutiklių ir valdiklio konfigūravimas',
            status='done'
        )
        db.session.add_all([t1, t2, t3, t4, t5, t6, t7, t8, t9])
        db.session.flush()

        # 4. Darbo laiko įrašai (WorkHours / HoursLogged - 3 lygmuo)
        if HoursLogged.query.count() == 0:
            today = date.today()
            hours_entries = [
                HoursLogged(
                    user_id=w1.id, project_id=p1.id, task_id=t1.id,
                    date=today - timedelta(days=5), start_time='08:00', end_time='17:00',
                    lunch_break=60, hours=8.0,
                    notes='Išvedžioti pagrindiniai maitinimo kabeliai rytiniame korpuse'
                ),
                HoursLogged(
                    user_id=w1.id, project_id=p1.id, task_id=t1.id,
                    date=today - timedelta(days=4), start_time='08:00', end_time='16:30',
                    lunch_break=30, hours=8.0,
                    notes='Sumontuotos 14 paskirstymo dėžučių ir atliktas žymėjimas'
                ),
                HoursLogged(
                    user_id=w1.id, project_id=p1.id, task_id=t3.id,
                    date=today - timedelta(days=3), start_time='08:30', end_time='17:00',
                    lunch_break=30, hours=8.0,
                    notes='Patikrinti 24 dūmų jutikliai ir sukalibruota centralė'
                ),
                HoursLogged(
                    user_id=w2.id, project_id=p2.id, task_id=t4.id,
                    date=today - timedelta(days=4), start_time='07:30', end_time='16:30',
                    lunch_break=60, hours=8.0,
                    notes='Sumontuoti aliuminio bėgeliai A ir B sektoriuose'
                ),
                HoursLogged(
                    user_id=w2.id, project_id=p2.id, task_id=t5.id,
                    date=today - timedelta(days=2), start_time='08:00', end_time='17:00',
                    lunch_break=60, hours=8.0,
                    notes='Sukelti ir pritvirtinti 40 saulės modulių, prijungtas 1 inverteris'
                ),
                HoursLogged(
                    user_id=w3.id, project_id=p3.id, task_id=t7.id,
                    date=today - timedelta(days=2), start_time='08:00', end_time='16:00',
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

    # 5. Atostogų ir nedarbingumo prašymai (LeaveRequest)
    if LeaveRequest.query.count() == 0:
        today = date.today()
        l1 = LeaveRequest(
            user_id=w1.id,
            type='vacation',
            start_date=today + timedelta(days=10),
            end_date=today + timedelta(days=14),
            notes='Kasmetinės rudens atostogos',
            status='pending'
        )
        l2 = LeaveRequest(
            user_id=w2.id,
            type='sick',
            start_date=today - timedelta(days=10),
            end_date=today - timedelta(days=8),
            notes='Peršalimas, nedarbingumo pažymėjimas',
            status='approved',
            reviewed_by=manager.id,
            reviewed_at=datetime.utcnow() - timedelta(days=10)
        )
        l3 = LeaveRequest(
            user_id=w3.id,
            type='vacation',
            start_date=today + timedelta(days=20),
            end_date=today + timedelta(days=22),
            notes='Šeimos šventė',
            status='approved',
            reviewed_by=manager.id,
            reviewed_at=datetime.utcnow() - timedelta(days=1)
        )
        db.session.add_all([l1, l2, l3])

    # 6. Pakvietimai (Invite)
    if Invite.query.count() == 0:
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
            print('Duomenu baze sekmingai uzpildyta prasmingais duomenimis!')
        else:
            print('Duomenu baze jau turi duomenu (naudokite --reset pilnam perrasymui).')
