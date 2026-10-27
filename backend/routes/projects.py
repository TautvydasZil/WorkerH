import math
from flask import Blueprint, request, jsonify

from extensions import db
from models import Project, Task, HoursLogged
from helpers import login_required, manager_or_admin_required, _validate_str, paginate_response

bp = Blueprint('projects', __name__, url_prefix='/api')


def _validate_coords(lat, lng):
    if lat is not None:
        if isinstance(lat, bool):
            raise ValueError('Platuma (latitude) turi būti skaičius')
        try:
            lat = float(lat)
        except (ValueError, TypeError):
            raise ValueError('Platuma (latitude) turi būti skaičius')
        if math.isnan(lat) or math.isinf(lat) or not (-90 <= lat <= 90):
            raise ValueError('Platuma (latitude) turi būti tarp -90 ir 90')
    if lng is not None:
        if isinstance(lng, bool):
            raise ValueError('Ilguma (longitude) turi būti skaičius')
        try:
            lng = float(lng)
        except (ValueError, TypeError):
            raise ValueError('Ilguma (longitude) turi būti skaičius')
        if math.isnan(lng) or math.isinf(lng) or not (-180 <= lng <= 180):
            raise ValueError('Ilguma (longitude) turi būti tarp -180 ir 180')
    return lat, lng


@bp.route('/projects', methods=['GET'])
@login_required
def get_projects():
    q = Project.query

    # Filtravimas pagal užbaigtumo būseną (?is_completed=true|false)
    is_completed_param = request.args.get('is_completed')
    if is_completed_param is not None and is_completed_param != '':
        val = is_completed_param.strip().lower()
        if val in ('true', '1', 'yes'):
            q = q.filter(Project.is_completed.is_(True))
        elif val in ('false', '0', 'no'):
            q = q.filter(Project.is_completed.is_(False))
        else:
            return jsonify({'error': 'is_completed filtras turi būti true arba false'}), 422

    # Filtravimas pagal pavadinimą arba paieškos frazę (?search=... arba ?name=...)
    search = (request.args.get('search') or request.args.get('name') or '').strip()
    if search:
        q = q.filter(Project.name.ilike(f'%{search}%'))

    # Filtravimas pagal adresą (?address=...)
    address = (request.args.get('address') or '').strip()
    if address:
        q = q.filter(Project.address.ilike(f'%{address}%'))

    projects = q.order_by(Project.name).all()
    return paginate_response([p.to_dict() for p in projects], '/api/projects')


@bp.route('/projects/<int:project_id>', methods=['GET'])
@login_required
def get_project(project_id):
    project = db.session.get(Project, project_id)
    if not project:
        return jsonify({'error': 'Projektas nerastas'}), 404
    return jsonify(project.to_dict()), 200


@bp.route('/projects/<int:project_id>/summary', methods=['GET'])
@login_required
def get_project_summary(project_id):
    """Sudėtinis resursas (panelė / suvestinė), sukonstruotas iš 3 esybių: Project, Task ir HoursLogged."""
    project = db.session.get(Project, project_id)
    if not project:
        return jsonify({'error': 'Projektas nerastas'}), 404

    tasks = Task.query.filter_by(project_id=project_id).order_by(Task.id.asc()).all()
    hours_entries = HoursLogged.query.filter_by(project_id=project_id).order_by(HoursLogged.date.desc()).all()

    hours_by_task = {}
    for h in hours_entries:
        hours_by_task[h.task_id] = round(hours_by_task.get(h.task_id, 0.0) + h.hours, 2)

    total_hours = round(sum(h.hours for h in hours_entries), 2)
    status_counts = {
        'todo': sum(1 for t in tasks if t.status == 'todo'),
        'in_progress': sum(1 for t in tasks if t.status == 'in_progress'),
        'done': sum(1 for t in tasks if t.status == 'done'),
    }

    return jsonify({
        'project': project.to_dict(),
        'statistics': {
            'total_tasks': len(tasks),
            'tasks_by_status': status_counts,
            'total_hours_logged': total_hours,
            'total_time_entries': len(hours_entries),
        },
        'tasks_breakdown': [
            {
                **t.to_dict(),
                'logged_hours': hours_by_task.get(t.id, 0.0),
            }
            for t in tasks
        ],
        '_links': {
            'self': f'/api/projects/{project.id}/summary',
            'project': f'/api/projects/{project.id}',
            'tasks': f'/api/projects/{project.id}/tasks',
        }
    }), 200


@bp.route('/projects', methods=['POST'])
@login_required
@manager_or_admin_required
def create_project():
    data = request.get_json(silent=True)
    if not isinstance(data, dict) or 'name' not in data or data.get('name') is None or str(data.get('name')).strip() == '':
        return jsonify({'error': 'Pavadinimas: laukas privalomas'}), 400

    try:
        name = _validate_str(data.get('name'), 'Pavadinimas', min_len=2, max_len=200)
        address = _validate_str(data.get('address', ''), 'Adresas', min_len=0, max_len=500, required=False) or None
        lat, lng = _validate_coords(data.get('latitude'), data.get('longitude'))
    except ValueError as e:
        return jsonify({'error': str(e)}), 422

    project = Project(
        name=name,
        latitude=lat,
        longitude=lng,
        address=address
    )
    db.session.add(project)
    db.session.commit()
    return jsonify(project.to_dict()), 201


@bp.route('/projects/<int:project_id>', methods=['PUT'])
@login_required
@manager_or_admin_required
def update_project(project_id):
    project = db.session.get(Project, project_id)
    if not project:
        return jsonify({'error': 'Projektas nerastas'}), 404

    data = request.get_json(silent=True)
    if not isinstance(data, dict) or not data:
        return jsonify({'error': 'Trūksta atnaujinamų duomenų'}), 400
    if 'name' in data and (data.get('name') is None or str(data.get('name')).strip() == ''):
        return jsonify({'error': 'Pavadinimas: laukas negali būti tuščias'}), 400

    try:
        if 'name' in data:
            project.name = _validate_str(data['name'], 'Pavadinimas', min_len=2, max_len=200)
        if 'address' in data:
            project.address = _validate_str(data['address'], 'Adresas', min_len=0, max_len=500, required=False) or None
        if 'latitude' in data or 'longitude' in data:
            lat, lng = _validate_coords(
                data.get('latitude', project.latitude),
                data.get('longitude', project.longitude)
            )
            if 'latitude' in data:
                project.latitude = lat
            if 'longitude' in data:
                project.longitude = lng
    except ValueError as e:
        return jsonify({'error': str(e)}), 422

    if 'is_completed' in data and isinstance(data['is_completed'], bool):
        project.is_completed = data['is_completed']

    db.session.commit()
    return jsonify(project.to_dict()), 200


@bp.route('/projects/<int:project_id>/complete', methods=['PATCH'])
@login_required
@manager_or_admin_required
def toggle_project_complete(project_id):
    project = db.session.get(Project, project_id)
    if not project:
        return jsonify({'error': 'Projektas nerastas'}), 404
    project.is_completed = not project.is_completed
    db.session.commit()
    return jsonify(project.to_dict()), 200


@bp.route('/projects/<int:project_id>', methods=['DELETE'])
@login_required
@manager_or_admin_required
def delete_project(project_id):
    project = db.session.get(Project, project_id)
    if not project:
        return jsonify({'error': 'Projektas nerastas'}), 404
    HoursLogged.query.filter_by(project_id=project_id).update({'project_id': None, 'task_id': None})
    Task.query.filter_by(project_id=project_id).delete()
    db.session.delete(project)
    db.session.commit()
    if request.args.get('with_body') == '1':
        return jsonify({'message': 'Projektas ištrintas'}), 200
    return '', 204
