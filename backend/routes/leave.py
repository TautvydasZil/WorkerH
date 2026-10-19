from datetime import datetime

from flask import Blueprint, request, jsonify

from extensions import db
from models import LeaveRequest
from helpers import login_required, manager_or_admin_required, get_current_user, _validate_str

bp = Blueprint('leave', __name__, url_prefix='/api')


@bp.route('/leave', methods=['POST'])
@login_required
def submit_leave():
    data = request.get_json(silent=True)
    user = get_current_user()

    if not isinstance(data, dict) or not all(k in data for k in ['type', 'start_date', 'end_date']):
        return jsonify({'error': 'Trūksta laukų'}), 400

    if data['type'] not in ('vacation', 'sick'):
        return jsonify({'error': 'Netinkamas prašymo tipas'}), 422

    try:
        start = datetime.strptime(str(data['start_date']), '%Y-%m-%d').date()
        end   = datetime.strptime(str(data['end_date']),   '%Y-%m-%d').date()
    except ValueError:
        return jsonify({'error': 'Netinkamas datos formatas'}), 422

    if end < start:
        return jsonify({'error': 'Pabaigos data negali būti ankstesnė už pradžios datą'}), 422

    try:
        notes = _validate_str(data.get('notes', ''), 'Pastabos', min_len=0, max_len=255, required=False)
    except ValueError as e:
        return jsonify({'error': str(e)}), 422

    overlap = LeaveRequest.query.filter(
        LeaveRequest.user_id == user.id,
        LeaveRequest.status == 'approved',
        LeaveRequest.start_date <= end,
        LeaveRequest.end_date >= start
    ).first()
    if overlap:
        return jsonify({'error': 'Pasirinktos datos jau dengiamos patvirtinto prašymo'}), 422

    auto_approve = data['type'] == 'sick'
    req = LeaveRequest(
        user_id=user.id,
        type=data['type'],
        start_date=start,
        end_date=end,
        notes=notes,
        status='approved' if auto_approve else 'pending',
        reviewed_at=datetime.utcnow() if auto_approve else None
    )
    db.session.add(req)
    db.session.commit()
    return jsonify(req.to_dict()), 201


@bp.route('/leave', methods=['GET'])
@login_required
def get_leave():
    user = get_current_user()
    if user.role in ('admin', 'manager'):
        target_id     = request.args.get('user_id', type=int)
        status_filter = request.args.get('status')
        q             = LeaveRequest.query
        if target_id:
            q = q.filter_by(user_id=target_id)
        if status_filter:
            q = q.filter_by(status=status_filter)
        requests = q.order_by(LeaveRequest.created_at.desc()).all()
    else:
        requests = LeaveRequest.query.filter_by(user_id=user.id).order_by(LeaveRequest.created_at.desc()).all()

    return jsonify([r.to_dict() for r in requests]), 200


@bp.route('/leave/<int:req_id>', methods=['GET'])
@login_required
def get_single_leave(req_id):
    user = get_current_user()
    req  = db.session.get(LeaveRequest, req_id)
    if not req:
        return jsonify({'error': 'Nerasta'}), 404
    if req.user_id != user.id and user.role not in ('admin', 'manager'):
        return jsonify({'error': 'Prieiga uždrausta'}), 403
    return jsonify(req.to_dict()), 200


@bp.route('/leave/<int:req_id>', methods=['DELETE'])
@login_required
def delete_leave(req_id):
    user = get_current_user()
    req  = db.session.get(LeaveRequest, req_id)
    if not req:
        return jsonify({'error': 'Nerasta'}), 404
    if req.user_id != user.id and user.role not in ('admin', 'manager'):
        return jsonify({'error': 'Prieiga uždrausta'}), 403
    if req.user_id == user.id and req.status != 'pending':
        return jsonify({'error': 'Galima atšaukti tik laukiančius prašymus'}), 422
    db.session.delete(req)
    db.session.commit()
    return jsonify({'message': 'Prašymas atšauktas'}), 200


@bp.route('/leave/<int:req_id>/review', methods=['PATCH'])
@login_required
@manager_or_admin_required
def review_leave(req_id):
    data     = request.get_json(silent=True)
    reviewer = get_current_user()

    if not isinstance(data, dict) or 'status' not in data:
        return jsonify({'error': 'Trūksta lauko "status"'}), 400
    if data['status'] not in ('approved', 'denied'):
        return jsonify({'error': 'Būsena turi būti "approved" arba "denied"'}), 422

    req = db.session.get(LeaveRequest, req_id)
    if not req:
        return jsonify({'error': 'Nerasta'}), 404
    if req.status != 'pending':
        return jsonify({'error': 'Galima peržiūrėti tik laukiančius prašymus'}), 422

    req.status      = data['status']
    req.reviewed_by = reviewer.id
    req.reviewed_at = datetime.utcnow()
    db.session.commit()
    return jsonify(req.to_dict()), 200

