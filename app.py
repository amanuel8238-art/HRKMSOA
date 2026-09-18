import os
from flask import Flask, render_template, redirect, url_for, request, flash, abort
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, User, Employee, Branch, Rank, Transfer
from functools import wraps

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'hrkmso-secret-key-2026')
# Render irratti Supabase (PostgreSQL) akka qabatuuf os.environ.get fayyanna
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///hrkmso.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Admin Qofaaf eeyyamuuf (RBAC Decorator)
def admin_required(f):
    @wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        if current_user.role != 'admin':
            abort(403) # Mirga hin qabdu
        return f(*args, **kwargs)
    return decorated_function

with app.app_context():
    db.create_all()
    
    # Dameewwan 39an hunda ofumaan database keessatti galchuuf (Dadar sirreeffameera)
    branches_list = [
        "Head Office (Finfinnee)", "Iluu Abaabor", "Jimmaa", "Bunoo Beddellee", 
        "Wallaggaa Bahaa", "Wallaggaa Lixaa", "Horo Guduruu Wallaggaa", "Qellem Wallaggaa",
        "Shawaa Bahaa", "Shawaa Lixaa", "Shawaa Kibba Lixaa", "Shawaa Kaabaa",
        "Baalee", "Baalee Bahaa", "Harargee Bahaa", "Harargee Lixaa",
        "Gujii Bahaa", "Gujii Lixaa", "Booranaa", "Booranaa Bahaa",
        "Arsii", "Arsii Lixaa", "GGLTO", "Dadar", "Magaalaa Shagar",
        "Baatuu", "Aggaroo", "Mayyaa", "Dodolaa", "Shanoo",
        "Aanaa Aallee", "Jimmaa Arjoo", "Eejeree", "Gursum", "Girawaa",
        "Habroo", "Dalloo Mannaa", "Martii", "Roobee"
    ]
    
    for b_name in branches_list:
        if not Branch.query.filter_by(name=b_name).first():
            db.session.add(Branch(name=b_name, location='Oromia'))
    db.session.commit()

# --- ROUTES ---

@app.route('/')
@login_required
def dashboard():
    emp_count = Employee.query.count()
    branch_count = Branch.query.count()
    transfer_count = Transfer.query.count()
    return render_template('dashboard.html', emp_count=emp_count, branch_count=branch_count, transfer_count=transfer_count)

@app.route('/employees')
@login_required
def employees():
    all_employees = Employee.query.all()
    all_branches = Branch.query.all()
    all_ranks = Rank.query.all()
    return render_template('employees.html', employees=all_employees, branches=all_branches, ranks=all_ranks)

# Hojjetaa haaraa dabaluuf (Deetaa guutuu foormii irraa fudhachuuf sirreeffame)
@app.route('/add_employee', methods=['POST'])
@login_required
def add_employee():
    full_name = request.form.get('full_name')
    unique_id = request.form.get('unique_id')
    gender = request.form.get('gender')
    branch_id = request.form.get('branch_id')
    rank_id = request.form.get('rank_id')
    rank_date = request.form.get('rank_date')
    hire_date = request.form.get('hire_date')
    birth_date = request.form.get('birth_date')
    rank_salary = request.form.get('rank_salary')
    location_allowance = request.form.get('location_allowance')
    food_allowance = request.form.get('food_allowance')
    education_level = request.form.get('education_level')
    field_of_study = request.form.get('field_of_study')
    job_position = request.form.get('job_position')
    status = request.form.get('status')
    
    new_emp = Employee(
        full_name=full_name,
        unique_id=unique_id,
        gender=gender,
        branch_id=branch_id,
        rank_id=rank_id,
        rank_date=rank_date,
        hire_date=hire_date,
        birth_date=birth_date,
        rank_salary=float(rank_salary) if rank_salary else 0.0,
        location_allowance=float(location_allowance) if location_allowance else 0.0,
        food_allowance=float(food_allowance) if food_allowance else 0.0,
        education_level=education_level,
        field_of_study=field_of_study,
        job_position=job_position,
        status=status
    )
    db.session.add(new_emp)
    db.session.commit()
    flash('Hojjetaan haaraan milkaa’inaan galmaa’eera!', 'success')
    return redirect(url_for('employees'))

@app.route('/branches')
@login_required
def branches():
    all_branches = Branch.query.all()
    return render_template('branches.html', branches=all_branches)

@app.route('/transfers')
@login_required
def transfers():
    all_transfers = Transfer.query.all()
    return render_template('transfers.html', transfers=all_transfers)

# Gulaataa Gonfoo (Ranks) - GET fi POST akka danda'u qindaa'era
@app.route('/ranks', methods=['GET', 'POST'])
@login_required
def ranks():
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')
        
        if name:
            new_rank = Rank(name=name, description=description)
            db.session.add(new_rank)
            db.session.commit()
            flash('Sadarkaan haaraan milkaa\'inaan galmaa\'eera!', 'success')
        else:
            flash('Maqaan sadarkaa guutamuu qaba!', 'danger')
            
        return redirect(url_for('ranks'))
    
    all_ranks = Rank.query.all()
    return render_template('ranks.html', ranks=all_ranks)

@app.route('/reports')
@login_required
def reports():
    return render_template('reports.html')

# Qindaa'ina - Admin Qofaaf
@app.route('/settings')
@admin_required
def settings():
    users = User.query.all()
    return render_template('settings.html', users=users)

# Fayyadamaa haaraa uumuu (Admin Qofaaf)
@app.route('/add_user', methods=['POST'])
@admin_required
def add_user():
    username = request.form.get('username')
    password = request.form.get('password')
    role = request.form.get('role', 'user')
    
    existing_user = User.query.filter_by(username=username).first()
    if existing_user:
        flash('Maqaan fayyadamaa kun kanaan dura jira!', 'danger')
    else:
        hashed_pw = generate_password_hash(password)
        new_user = User(username=username, password=hashed_pw, role=role)
        db.session.add(new_user)
        db.session.commit()
        flash('Fayyadamni haaraan milkaa\'inaan uumamee jira!', 'success')
        
    return redirect(url_for('settings'))

# Jecha icciti (Password) jijjiiruuf / Reset gochuuf
@app.route('/reset_password/<int:user_id>', methods=['POST'])
@admin_required
def reset_password(user_id):
    user = User.query.get_or_404(user_id)
    new_password = request.form.get('new_password')
    
    if new_password:
        user.password = generate_password_hash(new_password)
        db.session.commit()
        flash(f"Jechi iccitiitiif fayyadamaa '{user.username}' jijjiirameera!", 'success')
    else:
        flash('Jechi icciti haaraan duwwaa ta\'uu hin danda\'u!', 'danger')
        
    return redirect(url_for('settings'))

# Fayyadamaa haquuf (Delete User)
@app.route('/delete_user/<int:user_id>', methods=['POST'])
@admin_required
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    if user.username == 'admin':
        flash('Fayyadamaa Admin jalqabaa haquun hin danda\'amu!', 'danger')
    else:
        db.session.delete(user)
        db.session.commit()
        flash('Fayyadamaan milkaa\'inaan haqameera!', 'success')
    return redirect(url_for('settings'))

# --- AUTH ROUTES ---
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('dashboard'))
        flash('Maqaan fayyadamaa ykn jechi icciti dogoggordha!', 'danger')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

# Admin Jalqabaa uumuu
@app.before_request
def create_initial_data():
    if not User.query.filter_by(username='admin').first():
        hashed_pw = generate_password_hash('admin123')
        admin_user = User(username='admin', password=hashed_pw, role='admin')
        db.session.add(admin_user)
        db.session.commit()

if __name__ == '__main__':
    app.run(debug=True)