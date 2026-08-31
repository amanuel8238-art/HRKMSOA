from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

# Caasaa Raankii Hojjetootaa (Rank Structure)
RANKS_LIST = [
    "Komishinara General",
    "Komishinara Dooktar",
    "Komishinara Itti Aanaa",
    "Komishinara",
    "Kommanderii Guddaa",
    "Kommanderii",
    "Inspeekterii Olaanoo",
    "Inspeekterii Ibsaa",
    "Inspeekterii",
    "Sajjootti Olaanoo",
    "Sajjootti",
    "Hojjetaa Idilee"
]

class Employee(db.Model):
    __tablename__ = 'employees'
    
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(100), nullable=False)
    gender = db.Column(db.String(20), nullable=False)
    branch = db.Column(db.String(100), nullable=False)
    position = db.Column(db.String(100), nullable=False)
    rank = db.Column(db.String(50), nullable=False)