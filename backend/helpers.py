import re
from functools import wraps
from flask import session, jsonify, request
from extensions import db
from models import User

_EMAIL_RE = re.compile(r'^[^@\s]+@[^@\s]+\.[^@\s]+$')


def _validate_str(val, field, min_len=1, max_len=255, required=True):
    if val is None or str(val).strip() == '':
        if required:
            raise ValueError(f'{field}: laukas privalomas')
        return ''
    s = str(val).strip()
    if len(s) < min_len:
        raise ValueError(f'{field}: per trumpas (min {min_len} simboliai)')
    if len(s) > max_len:
        raise ValueError(f'{field}: per ilgas (maks {max_len} simboliai)')
    return s


def _validate_email(val, field='El. paštas'):
    s = _validate_str(val, field, max_len=255)
    if not _EMAIL_RE.match(s):
        raise ValueError(f'{field}: netinkamas formatas')
    return s.lower()


def get_current_user():
    # 1. Jei pateikta HTTP Authorization antraštė (pvz. iš Swagger arba Postman), pirmenybę teikiame jai
    auth = request.authorization
    if auth and auth.username and auth.password:
        user = User.query.filter_by(username=auth.username).first()
        if user and user.is_active and user.check_password(auth.password):
            return user

    # 2. Naršyklės sesijos slapukas
    user_id = session.get('user_id')
    if user_id:
        return db.session.get(User, user_id)

    return None


def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not get_current_user():
            return jsonify({'error': 'Nesate prisijungęs'}), 401
        return f(*args, **kwargs)
    return decorated


def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        user = get_current_user()
        if not user:
            return jsonify({'error': 'Nesate prisijungęs'}), 401
        if user.role != 'admin':
            return jsonify({'error': 'Prieiga uždrausta'}), 403
        return f(*args, **kwargs)
    return decorated


def manager_or_admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        user = get_current_user()
        if not user:
            return jsonify({'error': 'Nesate prisijungęs'}), 401
        if user.role not in ('manager', 'admin'):
            return jsonify({'error': 'Prieiga uždrausta'}), 403
        return f(*args, **kwargs)
    return decorated


def paginate_response(items, base_path=None):
    base_path = base_path or request.path
    total = len(items)
    raw_page = request.args.get('page')
    raw_per_page = request.args.get('per_page', request.args.get('limit'))
    envelope = request.args.get('envelope', '').lower() in ('1', 'true', 'yes')

    if raw_page is not None or raw_per_page is not None:
        try:
            page = int(raw_page) if raw_page is not None else 1
            per_page = int(raw_per_page) if raw_per_page is not None else 5
        except (ValueError, TypeError):
            return jsonify({'error': 'Puslapiavimo parametrai (page, per_page) turi būti sveikieji skaičiai'}), 422
        if page < 1 or per_page < 1 or per_page > 100:
            return jsonify({'error': 'page turi būti >= 1, o per_page tarp 1 ir 100'}), 422
        start = (page - 1) * per_page
        sliced = items[start:start + per_page]
        total_pages = max(1, (total + per_page - 1) // per_page)
    else:
        page = 1
        per_page = max(1, total)
        sliced = items
        total_pages = 1

    links = {
        'self': f'{base_path}?page={page}&per_page={per_page}',
        'first': f'{base_path}?page=1&per_page={per_page}',
        'last': f'{base_path}?page={total_pages}&per_page={per_page}',
        'prev': f'{base_path}?page={page - 1}&per_page={per_page}' if page > 1 else None,
        'next': f'{base_path}?page={page + 1}&per_page={per_page}' if page < total_pages else None,
    }

    if envelope:
        resp = jsonify({
            'items': sliced,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': total,
                'total_pages': total_pages,
            },
            '_links': links,
        })
    else:
        resp = jsonify(sliced)

    resp.headers['X-Total-Count'] = str(total)
    resp.headers['X-Page'] = str(page)
    resp.headers['X-Per-Page'] = str(per_page)
    resp.headers['X-Total-Pages'] = str(total_pages)
    link_parts = [f'<{url}>; rel="{rel}"' for rel, url in links.items() if url]
    resp.headers['Link'] = ', '.join(link_parts)
    return resp, 200

