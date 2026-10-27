from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from extensions import db


class User(db.Model):
    id            = db.Column(db.Integer, primary_key=True)
    username      = db.Column(db.String(80), unique=True, nullable=False)
    email         = db.Column(db.String(255), nullable=True, unique=True)
    password_hash = db.Column(db.String(200), nullable=False)
    first_name    = db.Column(db.String(80), nullable=False, default='')
    last_name     = db.Column(db.String(80), nullable=False, default='')
    role          = db.Column(db.String(20), default='worker')  # worker | manager | admin
    is_active     = db.Column(db.Boolean, default=True, nullable=False)
    created_at    = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'role': self.role,
            'is_active': self.is_active
        }


class Project(db.Model):
    id           = db.Column(db.Integer, primary_key=True)
    name         = db.Column(db.String(200), nullable=False)
    latitude     = db.Column(db.Float, nullable=True)
    longitude    = db.Column(db.Float, nullable=True)
    address      = db.Column(db.String(500))
    is_completed = db.Column(db.Boolean, default=False, nullable=False)
    created_at   = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'latitude': self.latitude,
            'longitude': self.longitude,
            'address': self.address,
            'is_completed': self.is_completed,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            '_links': {
                'self': f'/api/projects/{self.id}',
                'collection': '/api/projects',
                'tasks': f'/api/projects/{self.id}/tasks',
                'summary': f'/api/projects/{self.id}/summary',
            }
        }


class Task(db.Model):
    id          = db.Column(db.Integer, primary_key=True)
    project_id  = db.Column(db.Integer, db.ForeignKey('project.id'), nullable=False)
    title       = db.Column(db.String(200), nullable=False)
    description = db.Column(db.String(500), nullable=True)
    status      = db.Column(db.String(20), default='todo', nullable=False)  # todo | in_progress | done
    created_at  = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'project_id': self.project_id,
            'title': self.title,
            'name': self.title,
            'description': self.description,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            '_links': {
                'self': f'/api/projects/{self.project_id}/tasks/{self.id}',
                'collection': f'/api/projects/{self.project_id}/tasks',
                'project': f'/api/projects/{self.project_id}',
                'hours': f'/api/projects/{self.project_id}/tasks/{self.id}/hours',
            }
        }


class HoursLogged(db.Model):
    id          = db.Column(db.Integer, primary_key=True)
    user_id     = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    project_id  = db.Column(db.Integer, db.ForeignKey('project.id'), nullable=True)
    task_id     = db.Column(db.Integer, db.ForeignKey('task.id'), nullable=True)
    date        = db.Column(db.Date, nullable=False)
    hours       = db.Column(db.Float, nullable=False)
    start_time  = db.Column(db.String(5), nullable=True)
    end_time    = db.Column(db.String(5), nullable=True)
    lunch_break = db.Column(db.Integer, nullable=True)
    notes       = db.Column(db.String(255))
    created_at  = db.Column(db.DateTime, default=datetime.utcnow)


class LeaveRequest(db.Model):
    id          = db.Column(db.Integer, primary_key=True)
    user_id     = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    type        = db.Column(db.String(20), nullable=False)
    start_date  = db.Column(db.Date, nullable=False)
    end_date    = db.Column(db.Date, nullable=False)
    notes       = db.Column(db.String(255))
    status      = db.Column(db.String(20), default='pending')
    reviewed_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    reviewed_at = db.Column(db.DateTime, nullable=True)
    created_at  = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        days = (self.end_date - self.start_date).days + 1
        return {
            'id': self.id,
            'user_id': self.user_id,
            'type': self.type,
            'start_date': self.start_date.isoformat(),
            'end_date': self.end_date.isoformat(),
            'days': days,
            'notes': self.notes,
            'status': self.status,
            'reviewed_by': self.reviewed_by,
            'reviewed_at': self.reviewed_at.isoformat() if self.reviewed_at else None,
        }


class Invite(db.Model):
    id         = db.Column(db.Integer, primary_key=True)
    token      = db.Column(db.String(64), unique=True, nullable=False)
    email      = db.Column(db.String(255), nullable=False)
    role       = db.Column(db.String(20), nullable=False, default='worker')
    used       = db.Column(db.Boolean, default=False)
    expires_at = db.Column(db.DateTime, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class PasswordResetToken(db.Model):
    id         = db.Column(db.Integer, primary_key=True)
    user_id    = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    token      = db.Column(db.String(64), unique=True, nullable=False)
    expires_at = db.Column(db.DateTime, nullable=False)
    used       = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
