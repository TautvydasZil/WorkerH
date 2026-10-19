from flask import Blueprint, request, jsonify

from extensions import db
from models import Project, Task, HoursLogged
from helpers import login_required, manager_or_admin_required, _validate_str

bp = Blueprint('tasks', __name__, url_prefix='/api')

VALID_TASK_STATUSES = ('todo', 'in_progress', 'done')


def _get_project_and_task(project_id, task_id=None):
    project = db.session.get(Project, project_id)
    if not project:
        return None, None
    if task_id is None:
        return project, None
    task = Task.query.filter_by(id=task_id, project_id=project_id).first()
    return project, task


@bp.route('/projects/<int:project_id>/tasks', methods=['GET'])
@login_required
def get_project_tasks(project_id):
    project, _ = _get_project_and_task(project_id)
    if not project:
        return jsonify({'error': 'Projektas nerastas'}), 404
    tasks = Task.query.filter_by(project_id=project_id).order_by(Task.id.asc()).all()
    return jsonify([t.to_dict() for t in tasks]), 200


@bp.route('/projects/<int:project_id>/tasks/<int:task_id>', methods=['GET'])
@login_required
def get_project_task(project_id, task_id):
    project, task = _get_project_and_task(project_id, task_id)
    if not project:
        return jsonify({'error': 'Projektas nerastas'}), 404
    if not task:
        return jsonify({'error': 'Užduotis šiame projekte nerasta'}), 404
    return jsonify(task.to_dict()), 200


@bp.route('/projects/<int:project_id>/tasks', methods=['POST'])
@login_required
@manager_or_admin_required
def create_project_task(project_id):
    project, _ = _get_project_and_task(project_id)
    if not project:
        return jsonify({'error': 'Projektas nerastas'}), 404

    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({'error': 'Netinkamas užklausos formatas'}), 400

    raw_title = data.get('title') if 'title' in data else data.get('name')
    if raw_title is None or str(raw_title).strip() == '':
        return jsonify({'error': 'Užduoties pavadinimas (title): laukas privalomas'}), 400

    try:
        title = _validate_str(raw_title, 'Užduoties pavadinimas', min_len=2, max_len=200)
        description = _validate_str(
            data.get('description', ''), 'Aprašymas', min_len=0, max_len=500, required=False
        ) or None
    except ValueError as e:
        return jsonify({'error': str(e)}), 422

    status = data.get('status', 'todo')
    if status not in VALID_TASK_STATUSES:
        return jsonify({'error': f'Būsena turi būti viena iš: {", ".join(VALID_TASK_STATUSES)}'}), 422

    task = Task(
        project_id=project_id,
        title=title,
        description=description,
        status=status
    )
    db.session.add(task)
    db.session.commit()
    return jsonify(task.to_dict()), 201


@bp.route('/projects/<int:project_id>/tasks/<int:task_id>', methods=['PUT'])
@login_required
@manager_or_admin_required
def update_project_task(project_id, task_id):
    project, task = _get_project_and_task(project_id, task_id)
    if not project:
        return jsonify({'error': 'Projektas nerastas'}), 404
    if not task:
        return jsonify({'error': 'Užduotis šiame projekte nerasta'}), 404

    data = request.get_json(silent=True)
    if not isinstance(data, dict) or not data:
        return jsonify({'error': 'Trūksta atnaujinamų duomenų'}), 400

    has_title_key = 'title' in data or 'name' in data
    raw_title = data.get('title') if 'title' in data else data.get('name')
    if has_title_key and (raw_title is None or str(raw_title).strip() == ''):
        return jsonify({'error': 'Užduoties pavadinimas (title): laukas negali būti tuščias'}), 400

    try:
        if has_title_key:
            task.title = _validate_str(raw_title, 'Užduoties pavadinimas', min_len=2, max_len=200)
        if 'description' in data:
            task.description = _validate_str(
                data['description'], 'Aprašymas', min_len=0, max_len=500, required=False
            ) or None
    except ValueError as e:
        return jsonify({'error': str(e)}), 422

    if 'status' in data:
        if data['status'] not in VALID_TASK_STATUSES:
            return jsonify({'error': f'Būsena turi būti viena iš: {", ".join(VALID_TASK_STATUSES)}'}), 422
        task.status = data['status']

    db.session.commit()
    return jsonify(task.to_dict()), 200


@bp.route('/projects/<int:project_id>/tasks/<int:task_id>', methods=['DELETE'])
@login_required
@manager_or_admin_required
def delete_project_task(project_id, task_id):
    project, task = _get_project_and_task(project_id, task_id)
    if not project:
        return jsonify({'error': 'Projektas nerastas'}), 404
    if not task:
        return jsonify({'error': 'Užduotis šiame projekte nerasta'}), 404

    HoursLogged.query.filter_by(task_id=task_id).update({'task_id': None})
    db.session.delete(task)
    db.session.commit()
    return jsonify({'message': 'Užduotis ištrinta'}), 200


@bp.route('/tasks', methods=['GET'])
@login_required
def get_all_tasks():
    project_id = request.args.get('project_id', type=int)
    q = Task.query
    if project_id:
        q = q.filter_by(project_id=project_id)
    tasks = q.order_by(Task.project_id.asc(), Task.id.asc()).all()
    return jsonify([t.to_dict() for t in tasks]), 200
