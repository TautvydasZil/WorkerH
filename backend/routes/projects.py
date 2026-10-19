from flask import Blueprint, request, jsonify

from extensions import db
from models import Project, Task, HoursLogged
from helpers import login_required, manager_or_admin_required, _validate_str

bp = Blueprint('projects', __name__, url_prefix='/api')


def _validate_coords(lat, lng):
    if lat is not None:
        try:
            lat = float(lat)
        except (ValueError, TypeError):
            raise ValueError('Platuma (latitude) turi būti skaičius')
        if not (-90 <= lat <= 90):
            raise ValueError('Platuma (latitude) turi būti tarp -90 ir 90')
    if lng is not None:
        try:
            lng = float(lng)
        except (ValueError, TypeError):
            raise ValueError('Ilguma (longitude) turi būti skaičius')
        if not (-180 <= lng <= 180):
            raise ValueError('Ilguma (longitude) turi būti tarp -180 ir 180')
    return lat, lng


@bp.route('/projects', methods=['GET'])
@login_required
def get_projects():
    projects = Project.query.order_by(Project.name).all()
    return jsonify([p.to_dict() for p in projects]), 200


@bp.route('/projects/<int:project_id>', methods=['GET'])
@login_required
def get_project(project_id):
    project = db.session.get(Project, project_id)
    if not project:
        return jsonify({'error': 'Projektas nerastas'}), 404
    return jsonify(project.to_dict()), 200


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
    return jsonify({'message': 'Projektas ištrintas'}), 200

