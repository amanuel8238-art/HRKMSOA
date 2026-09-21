from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

db = SQLAlchemy()

# 1. To'annoo Fayyadamtootaa (User & Admin Role) - Damee isaanii waliin
class User(UserMixin, db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(50), nullable=False, default='user') # 'admin' ykn 'user'
    branch_id = db.Column(db.Integer, db.ForeignKey('branch.id'), nullable=True)

    branch = db.relationship('Branch', backref=db.backref('users', lazy=True))

# 2. Dameewwan (Branches - 39 branches including Dadar)
class Branch(db.Model):
    __tablename__ = 'branch'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    location = db.Column(db.String(150))

# 3. Sadarkaa / Gulantaa Gonfoo (Ranks)
class Rank(db.Model):
    __tablename__ = 'rank'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)

# 4. Hojjettoota (Employees)
class Employee(db.Model):
    __tablename__ = 'employee'
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(150), nullable=False)
    unique_id = db.Column(db.String(50), unique=True, nullable=True)
    gender = db.Column(db.String(20), nullable=True)
    branch_id = db.Column(db.Integer, db.ForeignKey('branch.id'), nullable=False)
    rank_id = db.Column(db.Integer, db.ForeignKey('rank.id'), nullable=False)
    rank_date = db.Column(db.String(50), nullable=True)
    hire_date = db.Column(db.String(50), nullable=True)
    birth_date = db.Column(db.String(50), nullable=True)
    rank_salary = db.Column(db.Float, nullable=True, default=0.0)
    location_allowance = db.Column(db.Float, nullable=True, default=0.0)
    food_allowance = db.Column(db.Float, nullable=True, default=0.0)
    education_level = db.Column(db.String(100), nullable=True)
    field_of_study = db.Column(db.String(150), nullable=True)
    job_position = db.Column(db.String(150), nullable=True)
    status = db.Column(db.String(50), default='Active')
    retirement_age = db.Column(db.Integer, default=55)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    branch = db.relationship('Branch', backref=db.backref('employees', lazy=True))
    rank = db.relationship('Rank', backref=db.backref('employees', lazy=True))

# 5. Jijjiirraa (Transfers) - app.py keessaa wajjin wal simsiifameera
class Transfer(db.Model):
    __tablename__ = 'transfer'
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employee.id'), nullable=False)
    from_branch_id = db.Column(db.Integer, db.ForeignKey('branch.id'), nullable=False)
    to_branch_id = db.Column(db.Integer, db.ForeignKey('branch.id'), nullable=False)
    reason = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(50), default='Pending') # Pending, Approved, Rejected
    approval_reason = db.Column(db.Text, nullable=True)
    transfer_date = db.Column(db.DateTime, default=datetime.utcnow)
    
    employee = db.relationship('Employee', backref=db.backref('transfers', lazy=True))
    from_branch = db.relationship('Branch', foreign_keys=[from_branch_id], backref=db.backref('outgoing_transfers', lazy=True))
    to_branch = db.relationship('Branch', foreign_keys=[to_branch_id], backref=db.backref('incoming_transfers', lazy=True))