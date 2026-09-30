from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

db = SQLAlchemy()

class User(UserMixin, db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(50), default='branch')  # 'admin' ykn 'branch'
    branch_id = db.Column(db.Integer, nullable=True)

class Branch(db.Model):
    __tablename__ = 'branch'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), unique=True, nullable=False)
    location = db.Column(db.String(150), nullable=True)
    employees = db.relationship('Employee', backref='branch', lazy=True)

class Rank(db.Model):
    __tablename__ = 'rank'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.Text, nullable=True)
    employees = db.relationship('Employee', backref='rank', lazy=True)

class Employee(db.Model):
    __tablename__ = 'employee'
    id = db.Column(db.Integer, primary_key=True)
    unique_id = db.Column(db.String(100), unique=True, nullable=True)
    full_name = db.Column(db.String(150), nullable=False)
    gender = db.Column(db.String(50), nullable=True)
    
    branch_id = db.Column(db.Integer, db.ForeignKey('branch.id'), nullable=True)
    rank_id = db.Column(db.Integer, db.ForeignKey('rank.id'), nullable=True)
    
    rank_date = db.Column(db.String(50), nullable=True)
    hire_date = db.Column(db.String(50), nullable=True)
    birth_date = db.Column(db.String(50), nullable=True)
    
    rank_salary = db.Column(db.Float, default=0.0)
    location_allowance = db.Column(db.Float, default=0.0)
    food_allowance = db.Column(db.Float, default=0.0)
    
    education_level = db.Column(db.String(100), nullable=True)
    field_of_study = db.Column(db.String(150), nullable=True)
    job_position = db.Column(db.String(150), nullable=True)
    status = db.Column(db.String(50), default='Active') # Active, Resigned, Terminated, etc.

    discipline_records = db.relationship('DisciplineRecord', backref='employee', cascade='all, delete-orphan', lazy=True)
    transfers = db.relationship('Transfer', backref='employee', cascade='all, delete-orphan', lazy=True)

class DisciplineRecord(db.Model):
    __tablename__ = 'discipline_record'
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employee.id'), nullable=False)
    penalty_type = db.Column(db.String(150), nullable=False)
    reason = db.Column(db.Text, nullable=True)
    date_given = db.Column(db.String(50), nullable=True)

class Transfer(db.Model):
    __tablename__ = 'transfer'
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employee.id'), nullable=False)
    from_branch_id = db.Column(db.String(100), nullable=True)
    to_branch_id = db.Column(db.Integer, nullable=True)
    reason = db.Column(db.Text, nullable=True)
    transfer_date = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(50), default='Pending') # Pending, Approved, Rejected