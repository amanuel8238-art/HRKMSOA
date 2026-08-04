import os
from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.secret_key = 'hrkmso_secret_key_secure'

db_url = os.environ.get('DATABASE_URL')
if db_url:
    if db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql://", 1)
    app.config['SQLALCHEMY_DATABASE_URI'] = db_url
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///hrkmso.db'

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    branch_name = db.Column(db.String(100), nullable=False)

class Branch(db.Model):
    __tablename__ = 'branches'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    employees = db.relationship('Employee', backref='branch_info', lazy=True)

class Employee(db.Model):
    __tablename__ = 'employees'
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(150), nullable=False)
    position = db.Column(db.String(100), nullable=False)
    rank = db.Column(db.String(50), nullable=False)
    education_level = db.Column(db.String(50), nullable=False)
    age = db.Column(db.Integer, nullable=False)
    branch_id = db.Column(db.Integer, db.ForeignKey('branches.id'), nullable=False)
    branch_name = db.Column(db.String(100), nullable=False)

with app.app_context():
    try:
        db.create_all()
        admin_user = User.query.filter_by(username='admin').first()
        if not admin_user:
            default_admin = User(username='admin', password='password123', branch_name='Head Office')
            db.session.add(default_admin)
            db.session.commit()
    except Exception as e:
        print(f"DB Init Error: {e}")

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        try:
            username = request.form.get('username')
            password = request.form.get('password')
            user = User.query.filter_by(username=username, password=password).first()
            if user:
                session['user_id'] = user.id
                session['username'] = user.username
                session['branch_name'] = user.branch_name
                return redirect(url_for('index'))
            else:
                return "Maqaa fayyadamaa ykn jecha darbii dogoggoraati! <a href='/login'>Irra deebi'ii yaali</a>"
        except Exception as e:
            return f"Login Error: {str(e)}"
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/')
def index():
    if 'username' not in session:
        return redirect(url_for('login'))
        
    try:
        current_branch = session.get('branch_name')
        selected_education = request.args.get('education')
        
        query = Employee.query
        if current_branch and current_branch != 'Head Office':
            query = query.filter_by(branch_name=current_branch)
        else:
            selected_branch = request.args.get('branch')
            if selected_branch and selected_branch != 'Head Office':
                query = query.filter_by(branch_name=selected_branch)
            
        if selected_education:
            query = query.filter_by(education_level=selected_education)
            
        employees = query.all()
        branches = Branch.query.all()
        
        return render_template('index.html', employees=employees, branches=branches, current_branch=current_branch)
    except Exception as e:
        return f"TEMPLATE/DB ERROR: {str(e)}"

@app.route('/add', methods=['POST'])
def add_employee():
    if 'username' not in session:
        return redirect(url_for('login'))
        
    try:
        full_name = request.form.get('full_name')
        position = request.form.get('position')
        rank = request.form.get('rank')
        education_level = request.form.get('education_level')
        age = request.form.get('age')
        
        branch_name = session.get('branch_name')
        if branch_name == 'Head Office':
            branch_name = request.form.get('branch_name')
        
        if full_name and position and rank and education_level and age and branch_name:
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