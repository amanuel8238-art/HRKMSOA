import os
from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.secret_key = 'hrkmso_secret_key_secure'

# Render fi Supabase Walitti Hidhuuf (DATABASE_URL qabachuuf)
db_url = os.environ.get('DATABASE_URL')

if db_url:
    # Render 'postgres://' deebisa, SQLAlchemy garuu 'postgresql://' gaafata
    if db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql://", 1)
    app.config['SQLALCHEMY_DATABASE_URI'] = db_url
else:
    # Local (Kompiitara kee) irratti yeroo yaaltu SQLite fayyadamuuf
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///hrkmso.db'

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# ==================== DATABASE MODELS ====================
class Branch(db.Model):
    __tablename__ = 'branches'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False) # Fakkeenyaaf: 'Head Office', 'Dadar'
    
    employees = db.relationship('Employee', backref='branch_info', lazy=True)

    def __repr__(self):
        return f"<Branch {self.name}>"


class Employee(db.Model):
    __tablename__ = 'employees'
    
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(150), nullable=False)
    position = db.Column(db.String(100), nullable=False)     # Qacaroo / Hooggansa
    rank = db.Column(db.String(50), nullable=False)         # Gonfoo (Rank)
    education_level = db.Column(db.String(50), nullable=False) # Sadarkaa Barnootaa (Degrii, Diploma, k.k.f)
    age = db.Column(db.Integer, nullable=False)             # Umrii
    
    branch_id = db.Column(db.Integer, db.ForeignKey('branches.id'), nullable=False)
    branch_name = db.Column(db.String(100), nullable=False)   # Maqaa Damee (Fkn: Dadar)

    def __repr__(self):
        return f"<Employee {self.full_name} - {self.branch_name}>"

# Table fi Database uumuu (App-n yeroo kaatu)
with app.app_context():
    db.create_all()

# ==================== ROUTES (WEB PAGES) ====================

@app.route('/')
def index():
    try:
        # Filter gochuuf (Damee, Sadarkaa Barnootaa, ykn Umrii irratti hundaa'uudhaan)
        selected_branch = request.args.get('branch')
        selected_education = request.args.get('education')
        
        query = Employee.query
        
        if selected_branch and selected_branch != 'Head Office':
            query = query.filter_by(branch_name=selected_branch)
            
        if selected_education:
            query = query.filter_by(education_level=selected_education)
            
        employees = query.all()
        branches = Branch.query.all()
        
        return render_template('index.html', employees=employees, branches=branches, selected_branch=selected_branch)
    except Exception as e:
        return f"TEMPLATE/DB ERROR: {str(e)}"

@app.route('/add', methods=['POST'])
def add_employee():
    try:
        full_name = request.form.get('full_name')
        position = request.form.get('position')
        rank = request.form.get('rank')
        education_level = request.form.get('education_level')
        age = request.form.get('age')
        branch_name = request.form.get('branch_name') # Fkn: Dadar
        
        if full_name and position and rank and education_level and age and branch_name:
            # Dursee branch sun table branches keessa jiraachuu isaa ilaalla yoo hin jirre uumna
            branch_obj = Branch.query.filter_by(name=branch_name).first()
            if not branch_obj:
                branch_obj = Branch(name=branch_name)
                db.session.add(branch_obj)
                db.session.commit()
            
            new_emp = Employee(
                full_name=full_name,
                position=position,
                rank=rank,
                education_level=education_level,
                age=int(age),
                branch_id=branch_obj.id,
                branch_name=branch_name
            )
            db.session.add(new_emp)
            db.session.commit()
    except Exception as e:
        print(f"Error: {e}")
        
    return redirect(url_for('index'))

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=True)