from datetime import datetime

from flask import Blueprint, request, jsonify

from extensions import db
from models import HoursLogged, Project, Task, LeaveRequest
from helpers import login_required, get_current_user, _validate_str

bp = Blueprint('hours', __name__, url_prefix='/api')


def _time_to_minutes(t):
    h, m = map(int, t.split(':'))
    if not (0 <= h <= 23 and 0 <= m <= 59) and not (h == 24 and m == 0):
        raise ValueError('Netinkamas laiko formatas')
    return h * 60 + m


def _overlapping_entry(user_id, date, new_start, new_end, exclude_id=None):
    entries = HoursLogged.query.filter(
        HoursLogged.user_id == user_id,
        HoursLogged.date == date,
        HoursLogged.start_time.isnot(None),
        HoursLogged.end_time.isnot(None)
    ).all()
    for e in entries:
        if exclude_id and e.id == exclude_id:
            continue
        s  = _time_to_minutes(e.start_time)
        en = _time_to_minutes(e.end_time)
        if new_start < en and new_end > s:
            return e
    return None


def _hours_to_dict(e, project_map=None, task_map=None):
    project_map = project_map or {}
    task_map    = task_map or {}
    return {
        'id': e.id,
        'user_id': e.user_id,
        'project_id': e.project_id,
        'project_name': project_map.get(e.project_id),
        'task_id': e.task_id,
        'task_title': task_map.get(e.task_id),
        'date': e.date.isoformat(),
        'hours': e.hours,
        'start_time': e.start_time,
        'end_time': e.end_time,
        'lunch_break': e.lunch_break,
        'notes': e.notes
    }


def _enrich_entries(entries):
    proj_ids = {e.project_id for e in entries if e.project_id}
    task_ids = {e.task_id for e in entries if e.task_id}
    project_map = {p.id: p.name for p in Project.query.filter(Project.id.in_(proj_ids)).all()} if proj_ids else {}
    task_map    = {t.id: t.title for t in Task.query.filter(Task.id.in_(task_ids)).all()} if task_ids else {}
    return [_hours_to_dict(e, project_map, task_map) for e in entries]


def _validate_and_parse_hours_payload(data, target_user_id, exclude_entry_id=None):
    if not isinstance(data, dict) or not all(k in data for k in ['date', 'start_time', 'end_time']):
        return None, (jsonify({'error': 'Trūksta privalomų laukų (date, start_time, end_time)'}), 400)

    try:
        date = datetime.strptime(str(data['date']), '%Y-%m-%d').date()
    except (ValueError, TypeError):
        return None, (jsonify({'error': 'Netinkamas datos formatas (turi būti YYYY-MM-DD)'}), 422)

    try:
        new_start = _time_to_minutes(str(data['start_time']))
        new_end   = _time_to_minutes(str(data['end_time']))
    except (ValueError, AttributeError, TypeError):
        return None, (jsonify({'error': 'Netinkamas laiko formatas (turi būti HH:MM)'}), 422)

    try:
        notes = _validate_str(data.get('notes', ''), 'Pastabos', min_len=0, max_len=255, required=False)
    except ValueError as e:
        return None, (jsonify({'error': str(e)}), 422)

    try:
        raw_lunch = data.get('lunch_break')
        lunch_break = int(raw_lunch) if raw_lunch is not None and raw_lunch != '' else 0
        if lunch_break < 0 or lunch_break > 480:
            return None, (jsonify({'error': 'Pietų pertrauka turi būti tarp 0 ir 480 min.'}), 422)
    except (ValueError, TypeError):
        return None, (jsonify({'error': 'Pietų pertrauka turi būti sveikasis skaičius'}), 422)

    total_minutes = new_end - new_start - lunch_break
    if total_minutes <= 0:
        return None, (jsonify({
            'error': 'Darbo laikas turi būti teigiamas (patikrinkite pradžios, pabaigos laiką ir pietų pertrauką)'
        }), 422)
    if total_minutes > 24 * 60:
        return None, (jsonify({'error': 'Valandos negali viršyti 24'}), 422)

    conflict = LeaveRequest.query.filter(
        LeaveRequest.user_id == target_user_id,
        LeaveRequest.status == 'approved',
        LeaveRequest.start_date <= date,
        LeaveRequest.end_date >= date
    ).first()
    if conflict:
        type_str = 'atostogų' if conflict.type == 'vacation' else 'nedarbingumo'
        return None, (jsonify({
            'error': f'Šią dieną turite patvirtintą {type_str} prašymą — darbo valandų įvesti negalima'
        }), 422)

    overlap = _overlapping_entry(target_user_id, date, new_start, new_end, exclude_id=exclude_entry_id)
    if overlap:
        return None, (jsonify({
            'error': f'Šis laikas persidengia su jau įvestu įrašu ({overlap.start_time}–{overlap.end_time})'
        }), 422)

    return {
        'date': date,
        'start_time': str(data['start_time']),
        'end_time': str(data['end_time']),
        'lunch_break': lunch_break if lunch_break > 0 else None,
        'hours': round(total_minutes / 60, 2),
        'notes': notes
    }, None


# ============================================================================
# 3-ojo lygmens hierarchiniai maršrutai:
# /api/projects/<project_id>/tasks/<task_id>/hours
# ============================================================================

def _verify_project_and_task(project_id, task_id):
    project = db.session.get(Project, project_id)
    if not project:
        return None, None, (jsonify({'error': 'Projektas nerastas'}), 404)
    task = Task.query.filter_by(id=task_id, project_id=project_id).first()
    if not task:
        return project, None, (jsonify({'error': 'Užduotis šiame projekte nerasta'}), 404)
    return project, task, None


@bp.route('/projects/<int:project_id>/tasks/<int:task_id>/hours', methods=['GET'])
@login_required
def get_task_hours(project_id, task_id):
    project, task, err = _verify_project_and_task(project_id, task_id)
    if err:
        return err

    user = get_current_user()
    q = HoursLogged.query.filter_by(project_id=project_id, task_id=task_id)
    if user.role not in ('admin', 'manager'):
        q = q.filter_by(user_id=user.id)
    else:
        target_id = request.args.get('user_id', type=int)
        if target_id:
            q = q.filter_by(user_id=target_id)

    entries = q.order_by(HoursLogged.date.desc(), HoursLogged.id.desc()).all()
    project_map = {project.id: project.name}
    task_map    = {task.id: task.title}
    return jsonify([_hours_to_dict(e, project_map, task_map) for e in entries]), 200


@bp.route('/projects/<int:project_id>/tasks/<int:task_id>/hours/<int:entry_id>', methods=['GET'])
@login_required
def get_task_hours_entry(project_id, task_id, entry_id):
    project, task, err = _verify_project_and_task(project_id, task_id)
    if err:
        return err

    entry = HoursLogged.query.filter_by(id=entry_id, project_id=project_id, task_id=task_id).first()
    if not entry:
        return jsonify({'error': 'Darbo laiko įrašas šioje užduotyje nerastas'}), 404

    user = get_current_user()
    if entry.user_id != user.id and user.role not in ('admin', 'manager'):
        return jsonify({'error': 'Prieiga uždrausta'}), 403

    return jsonify(_hours_to_dict(entry, {project.id: project.name}, {task.id: task.title})), 200


@bp.route('/projects/<int:project_id>/tasks/<int:task_id>/hours', methods=['POST'])
@login_required
def create_task_hours(project_id, task_id):
    project, task, err = _verify_project_and_task(project_id, task_id)
    if err:
        return err

    user = get_current_user()
    data = request.get_json(silent=True)
    parsed, val_err = _validate_and_parse_hours_payload(data, user.id)
    if val_err:
        return val_err

    entry = HoursLogged(
        user_id=user.id,
        project_id=project.id,
        task_id=task.id,
        date=parsed['date'],
        hours=parsed['hours'],
        start_time=parsed['start_time'],
        end_time=parsed['end_time'],
        lunch_break=parsed['lunch_break'],
        notes=parsed['notes']
    )
    db.session.add(entry)
    db.session.commit()

    res = _hours_to_dict(entry, {project.id: project.name}, {task.id: task.title})
    res['message'] = 'Valandos įvestos!'
    return jsonify(res), 201


@bp.route('/projects/<int:project_id>/tasks/<int:task_id>/hours/<int:entry_id>', methods=['PUT'])
@login_required
def update_task_hours(project_id, task_id, entry_id):
    project, task, err = _verify_project_and_task(project_id, task_id)
    if err:
        return err

    entry = HoursLogged.query.filter_by(id=entry_id, project_id=project_id, task_id=task_id).first()
    if not entry:
        return jsonify({'error': 'Darbo laiko įrašas šioje užduotyje nerastas'}), 404

    user = get_current_user()
    if entry.user_id != user.id and user.role not in ('admin', 'manager'):
        return jsonify({'error': 'Prieiga uždrausta'}), 403

    data = request.get_json(silent=True)
    parsed, val_err = _validate_and_parse_hours_payload(data, entry.user_id, exclude_entry_id=entry.id)
    if val_err:
        return val_err

    entry.date        = parsed['date']
    entry.start_time  = parsed['start_time']
    entry.end_time    = parsed['end_time']
    entry.lunch_break = parsed['lunch_break']
    entry.hours       = parsed['hours']
    entry.notes       = parsed['notes']
    db.session.commit()

    return jsonify(_hours_to_dict(entry, {project.id: project.name}, {task.id: task.title})), 200


@bp.route('/projects/<int:project_id>/tasks/<int:task_id>/hours/<int:entry_id>', methods=['DELETE'])
@login_required
def delete_task_hours(project_id, task_id, entry_id):
    project, task, err = _verify_project_and_task(project_id, task_id)
    if err:
        return err

    entry = HoursLogged.query.filter_by(id=entry_id, project_id=project_id, task_id=task_id).first()
    if not entry:
        return jsonify({'error': 'Darbo laiko įrašas šioje užduotyje nerastas'}), 404

    user = get_current_user()
    if entry.user_id != user.id and user.role not in ('admin', 'manager'):
        return jsonify({'error': 'Prieiga uždrausta'}), 403

    db.session.delete(entry)
    db.session.commit()
    return jsonify({'message': 'Darbo laiko įrašas ištrintas'}), 200


# ============================================================================
# Bendrieji darbo valandų maršrutai (/api/hours)
# ============================================================================

@bp.route('/hours', methods=['POST'])
@login_required
def log_hours():
    data = request.get_json(silent=True)
    user = get_current_user()

    parsed, val_err = _validate_and_parse_hours_payload(data, user.id)
    if val_err:
        return val_err

    project_id = data.get('project_id') or None
    task_id    = data.get('task_id') or None

    if project_id:
        project = db.session.get(Project, project_id)
        if not project:
            return jsonify({'error': 'Projektas nerastas'}), 404

    if task_id:
        task = db.session.get(Task, task_id)
        if not task:
            return jsonify({'error': 'Užduotis nerasta'}), 404
        if project_id and task.project_id != int(project_id):
            return jsonify({'error': 'Užduotis nepriklauso pasirinktam projektui'}), 422
        if not project_id:
            project_id = task.project_id

    entry = HoursLogged(
        user_id=user.id,
        project_id=project_id,
        task_id=task_id,
        date=parsed['date'],
        hours=parsed['hours'],
        start_time=parsed['start_time'],
        end_time=parsed['end_time'],
        lunch_break=parsed['lunch_break'],
        notes=parsed['notes']
    )
    db.session.add(entry)
    db.session.commit()
    res = _enrich_entries([entry])[0]
    res['message'] = 'Valandos įvestos!'
    return jsonify(res), 201


@bp.route('/hours', methods=['GET'])
@login_required
def get_hours():
    user = get_current_user()
    if user.role in ('admin', 'manager'):
        target_id  = request.args.get('user_id', type=int)
        project_id = request.args.get('project_id', type=int)
        task_id    = request.args.get('task_id', type=int)
        date_from  = request.args.get('date_from')
        date_to    = request.args.get('date_to')
        q          = HoursLogged.query
        if target_id:
            q = q.filter_by(user_id=target_id)
        if project_id:
            q = q.filter_by(project_id=project_id)
        if task_id:
            q = q.filter_by(task_id=task_id)
        if date_from:
            try:
                q = q.filter(HoursLogged.date >= datetime.strptime(date_from, '%Y-%m-%d').date())
            except ValueError:
                pass
        if date_to:
            try:
                q = q.filter(HoursLogged.date <= datetime.strptime(date_to, '%Y-%m-%d').date())
            except ValueError:
                pass
        entries = q.order_by(HoursLogged.date.desc(), HoursLogged.id.desc()).all()
    else:
        entries = HoursLogged.query.filter_by(user_id=user.id).order_by(HoursLogged.date.desc(), HoursLogged.id.desc()).all()

    return jsonify(_enrich_entries(entries)), 200


@bp.route('/hours/<int:entry_id>', methods=['GET'])
@login_required
def get_single_hours(entry_id):
    user  = get_current_user()
    entry = db.session.get(HoursLogged, entry_id)
    if not entry:
        return jsonify({'error': 'Nerasta'}), 404
    if entry.user_id != user.id and user.role not in ('admin', 'manager'):
        return jsonify({'error': 'Prieiga uždrausta'}), 403
    return jsonify(_enrich_entries([entry])[0]), 200


@bp.route('/hours/<int:entry_id>', methods=['PUT'])
@login_required
def update_hours(entry_id):
    user  = get_current_user()
    entry = db.session.get(HoursLogged, entry_id)
    if not entry:
        return jsonify({'error': 'Nerasta'}), 404
    if entry.user_id != user.id and user.role not in ('admin', 'manager'):
        return jsonify({'error': 'Prieiga uždrausta'}), 403

    data = request.get_json(silent=True)
    parsed, val_err = _validate_and_parse_hours_payload(data, entry.user_id, exclude_entry_id=entry_id)
    if val_err:
        return val_err

    project_id = data.get('project_id', entry.project_id)
    task_id    = data.get('task_id', entry.task_id)

    if project_id and not db.session.get(Project, project_id):
        return jsonify({'error': 'Projektas nerastas'}), 404
    if task_id:
        task = db.session.get(Task, task_id)
        if not task:
            return jsonify({'error': 'Užduotis nerasta'}), 404
        if project_id and task.project_id != int(project_id):
            return jsonify({'error': 'Užduotis nepriklauso pasirinktam projektui'}), 422

    entry.date        = parsed['date']
    entry.start_time  = parsed['start_time']
    entry.end_time    = parsed['end_time']
    entry.lunch_break = parsed['lunch_break']
    entry.hours       = parsed['hours']
    entry.project_id  = project_id or None
    entry.task_id     = task_id or None
    entry.notes       = parsed['notes']
    db.session.commit()

    return jsonify(_enrich_entries([entry])[0]), 200


@bp.route('/hours/<int:entry_id>', methods=['DELETE'])
@login_required
def delete_hours(entry_id):
    user  = get_current_user()
    entry = db.session.get(HoursLogged, entry_id)
    if not entry:
        return jsonify({'error': 'Nerasta'}), 404
    if entry.user_id != user.id and user.role not in ('admin', 'manager'):
        return jsonify({'error': 'Prieiga uždrausta'}), 403
    db.session.delete(entry)
    db.session.commit()
    return jsonify({'message': 'Ištrinta'}), 200
