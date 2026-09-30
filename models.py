from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    role = db.Column(db.String(50), nullable=False, default='branch')
    branch_id = db.Column(db.Integer, db.ForeignKey('branch.id'), nullable=True)

class Branch(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    employees = db.relationship('Employee', backref='branch', lazy=True)

class Rank(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)

class Employee(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(150), nullable=False)
    job_position = db.Column(db.String(100), nullable=False)
    education_level = db.Column(db.String(50), nullable=True)
    field_of_study = db.Column(db.String(100), nullable=True)
    branch_id = db.Column(db.Integer, db.ForeignKey('branch.id'), nullable=False)
    rank_id = db.Column(db.Integer, db.ForeignKey('rank.id'), nullable=False)
    rank = db.relationship('Rank', backref='employees', lazy=True)

class Transfer(db.Model):
    id = db.Column(db.Integer, primary_key=True)

class DisciplineRecord(db.Model):
    id = db.Column(db.Integer, primary_key=True)

class PromotionAssessment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employee.id'), nullable=False)
    performance_score = db.Column(db.Float, default=0.0)
    education_score = db.Column(db.Float, default=0.0)
    discipline_score = db.Column(db.Float, default=0.0)
    law_compliance_score = db.Column(db.Float, default=0.0)
    experience_score = db.Column(db.Float, default=0.0)
    service_spirit_score = db.Column(db.Float, default=0.0)
    total_score = db.Column(db.Float, default=0.0)
    current_rank_id = db.Column(db.Integer, nullable=True)
    next_rank_id = db.Column(db.Integer, nullable=True)
    status = db.Column(db.String(50), default='Pending Head Office Review')
    
    employee = db.relationship('Employee', backref='assessments', lazy=True)
    next_rank = db.relationship('Rank', foreign_keys=[next_rank_id], lazy=True)