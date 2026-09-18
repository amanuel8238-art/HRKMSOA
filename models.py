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
    branch_id = db.Column(db.Integer, db.ForeignKey('branch.id'), nullable=True) # Fayyadamaan damee kam akka qabu agarsiisa

    # Relationship to Branch
    branch = db.relationship('Branch', backref=db.backref('users', lazy=True))

# 2. Dameewwan (Branches - 39 branches including Dadar)
class Branch(db.Model):
    __tablename__ = 'branch'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False) # Fakkeenyaaf: Dadar, fi kkf
    location = db.Column(db.String(150))

# 3. Sadarkaa / Gulantaa Gonfoo (Ranks)
class Rank(db.Model):
    __tablename__ = 'rank'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False) # Fakkeenyaaf: Raankii / Gulantaa hojjettootaa
    description = db.Column(db.Text, nullable=True) # Kolonii ibsaa (description)

# 4. Hojjettoota (Employees - Deetaa guutuu fi kan duraa qabatetti deebi'e)
class Employee(db.Model):
    __tablename__ = 'employee'
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(150), nullable=False)
    unique_id = db.Column(db.String(50), unique=True, nullable=True) # ID Addaa
    gender = db.Column(db.String(20), nullable=True)
    branch_id = db.Column(db.Integer, db.ForeignKey('branch.id'), nullable=False)
    rank_id = db.Column(db.Integer, db.ForeignKey('rank.id'), nullable=False)
    rank_date = db.Column(db.String(50), nullable=True) # Guyyaa Gulaantaa Gonfoo Argate
    hire_date = db.Column(db.String(50), nullable=True) # Guyyaa Qacarichaa
    birth_date = db.Column(db.String(50), nullable=True) # Guyyaa Dhalootaa
    rank_salary = db.Column(db.Float, nullable=True, default=0.0) # Mindaa Gulaantaa Gonfoo
    location_allowance = db.Column(db.Float, nullable=True, default=0.0) # Mindaa Idoo
    food_allowance = db.Column(db.Float, nullable=True, default=0.0) # Durgoo Nyaataa
    education_level = db.Column(db.String(100), nullable=True) # Sadarkaa Barumsaa
    field_of_study = db.Column(db.String(150), nullable=True) # Gosa Barumsaa
    job_position = db.Column(db.String(150), nullable=True) # Gita Hojii
    status = db.Column(db.String(50), default='Active') # Haala / Status
    retirement_age = db.Column(db.Integer, default=55) # Umrii sooramaa 55
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    branch = db.relationship('Branch', backref=db.backref('employees', lazy=True))
    rank = db.relationship('Rank', backref=db.backref('employees', lazy=True))

# 5. Jijjiirraa (Transfers)
class Transfer(db.Model):
    __tablename__ = 'transfer'
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employee.id'), nullable=False)
    from_branch = db.Column(db.String(150), nullable=False)
    to_branch = db.Column(db.String(150), nullable=False)
    transfer_date = db.Column(db.DateTime, default=datetime.utcnow)
    
    employee = db.relationship('Employee', backref=db.backref('transfers', lazy=True))