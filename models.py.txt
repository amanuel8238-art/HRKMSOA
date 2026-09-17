from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

db = SQLAlchemy()

# 1. To'annoo Fayyadamtootaa (User & Admin Role)
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(50), nullable=False, default='user') # 'admin' ykn 'user'

# 2. Dameewwan (Branches - 39 branches including Dadar)
class Branch(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False) # Fakkeenyaaf: Dadar, fi kkf
    location = db.Column(db.String(150))

# 3. Sadarkaa / Gulantaa Gonfoo (Ranks)
class Rank(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False) # Fakkeenyaaf: Raankii / Gulantaa hojjettootaa

# 4. Hojjettoota (Employees)
class Employee(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(150), nullable=False)
    gender = db.Column(db.String(10))
    branch_id = db.Column(db.Integer, db.ForeignKey('branch.id'), nullable=False)
    rank_id = db.Column(db.Integer, db.ForeignKey('rank.id'), nullable=False)
    retirement_age = db.Column(db.Integer, default=55) # Umrii sooramaa 55
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    branch = db.relationship('Branch', backref=db.backref('employees', lazy=True))
    rank = db.relationship('Rank', backref=db.backref('employees', lazy=True))

# 5. Jijjiirraa (Transfers)
class Transfer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employee.id'), nullable=False)
    from_branch = db.Column(db.String(150), nullable=False)
    to_branch = db.Column(db.String(150), nullable=False)
    transfer_date = db.Column(db.DateTime, default=datetime.utcnow)
    
    employee = db.relationship('Employee', backref=db.backref('transfers', lazy=True))