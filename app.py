import os
from flask import Flask, render_template, redirect, url_for, request, flash, abort
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, User, Employee, Branch, Rank, Transfer
from functools import wraps
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'hrkmso-secret-key-2026')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///hrkmso.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

# Admin Qofaaf eeyyamuuf (RBAC Decorator)
def admin_required(f):
    @wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        if current_user.role != 'admin':
            abort(403)
        return f(*args, **kwargs)
    return decorated_function

# Rank input (ID ykn Name) sirriitti barbaaduuf
def resolve_rank_id(rank_input):
    if not rank_input:
        return None
    if str(rank_input).isdigit():
        return int(rank_input)
    else:
        r_obj = Rank.query.filter_by(name=rank_input).first()
        if not r_obj:
            r_obj = Rank.query.filter(Rank.name.ilike(rank_input.strip())).first()
        return r_obj.id if r_obj else None

with app.app_context():
    db.create_all()
    
    # 1. Admin Jalqabaa Uumuu
    if not User.query.filter_by(username='admin').first():
        hashed_pw = generate_password_hash('admin123')
        admin_user = User(username='admin', password=hashed_pw, role='admin', branch_id=None)
        db.session.add(admin_user)

    # 2. Sadarkaa (Rank) Jalqabaa akka hin dhabamne (Fallback Rank) uumuu
    if not Rank.query.first():
        default_rank = Rank(name='Standard Rank', description='Default system rank')
        db.session.add(default_rank)

    # 3. Dameewwan 39an hunda ofumaan database keessatti galchuuf (Dadar included)
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
    if current_user.role == 'admin':
        emp_count = Employee.query.count()
        branch_count = Branch.query.count()
        transfer_count = Transfer.query.count()
    else:
        emp_count = Employee.query.filter_by(branch_id=current_user.branch_id).count() if current_user.branch_id else 0
        branch_count = 1
        if hasattr(Transfer, 'from_branch_id') and current_user.branch_id:
            transfer_count = Transfer.query.filter_by(from_branch_id=current_user.branch_id).count()
        else:
            transfer_count = 0

    return render_template('dashboard.html', emp_count=emp_count, branch_count=branch_count, transfer_count=transfer_count)

@app.route('/employees')
@login_required
def employees():
    branch_id = request.args.get('branch_id')
    rank = request.args.get('rank')
    gender = request.args.get('gender')
    search_query = request.args.get('search', '')

    query = Employee.query

    if current_user.role != 'admin':
        branch_id = current_user.branch_id
        query = query.filter_by(branch_id=branch_id)
    elif branch_id:
        query = query.filter_by(branch_id=branch_id)

    if rank:
        query = query.join(Employee.rank).filter(db.or_(Rank.name == rank, Rank.id == rank))
    
    # Fooyya'iinsi Gender Filter: Dhalaa ykn Dubartii ta'uu isaa hubatee akka fidu
    if gender:
        if gender in ['Dhalaa', 'Dubartii']:
            query = query.filter(db.or_(Employee.gender == 'Dhalaa', Employee.gender == 'Dubartii'))
        else:
            query = query.filter_by(gender=gender)

    if search_query:
        query = query.filter(
            db.or_(
                Employee.full_name.ilike(f'%{search_query}%'),
                Employee.unique_id.ilike(f'%{search_query}%')
            )
        )

    all_employees = query.all()
    all_branches = Branch.query.all()
    all_ranks = Rank.query.all()
    
    return render_template('employees.html', employees=all_employees, branches=all_branches, ranks=all_ranks)

# Hojjetaa haaraa dabaluuf
@app.route('/add_employee', methods=['POST'])
@login_required
def add_employee():
    full_name = request.form.get('full_name')
    unique_id = request.form.get('unique_id')
    gender = request.form.get('gender')
    
    if current_user.role == 'admin':
        branch_id = request.form.get('branch_id')
    else:
        branch_id = current_user.branch_id

    rank_input = request.form.get('rank_id')
    rank_id = resolve_rank_id(rank_input)
    if not rank_id:
        first_rank = Rank.query.first()
        rank_id = first_rank.id if first_rank else 1

    rank_date = request.form.get('rank_date')
    hire_date = request.form.get('hire_date')
    birth_date = request.form.get('birth_date')
    rank_salary = request.form.get('rank_salary')
    location_allowance = request.form.get('location_allowance')
    food_allowance = request.form.get('food_allowance')
    education_level = request.form.get('education_level')
    field_of_study = request.form.get('field_of_study')
    job_position = request.form.get('job_position')
    status = request.form.get('status', 'Active')
    
    new_emp = Employee(
        full_name=full_name,
        unique_id=unique_id,
        gender=gender,
        branch_id=int(branch_id) if branch_id else None,
        rank_id=rank_id,
        rank_date=rank_date if rank_date else None,
        hire_date=hire_date if hire_date else None,
        birth_date=birth_date if birth_date else None,
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

# Hojjetaa Jiru Gulaaluuf
@app.route('/edit_employee/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_employee(id):
    emp = Employee.query.get_or_404(id)
    
    if current_user.role != 'admin' and emp.branch_id != current_user.branch_id:
        abort(403)

    if request.method == 'POST':
        emp.full_name = request.form.get('full_name')
        emp.unique_id = request.form.get('unique_id')
        emp.gender = request.form.get('gender')
        
        if current_user.role == 'admin':
            branch_id = request.form.get('branch_id')
            emp.branch_id = int(branch_id) if branch_id else None

        rank_input = request.form.get('rank_id')
        if rank_input:
            resolved_rank_id = resolve_rank_id(rank_input)
            if resolved_rank_id:
                emp.rank_id = resolved_rank_id
        
        emp.rank_date = request.form.get('rank_date') if request.form.get('rank_date') else None
        emp.hire_date = request.form.get('hire_date') if request.form.get('hire_date') else None
        emp.birth_date = request.form.get('birth_date') if request.form.get('birth_date') else None
        
        rank_salary = request.form.get('rank_salary')
        location_allowance = request.form.get('location_allowance')
        food_allowance = request.form.get('food_allowance')
        
        emp.rank_salary = float(rank_salary) if rank_salary else 0.0
        emp.location_allowance = float(location_allowance) if location_allowance else 0.0
        emp.food_allowance = float(food_allowance) if food_allowance else 0.0
        
        emp.education_level = request.form.get('education_level')
        emp.field_of_study = request.form.get('field_of_study')
        emp.job_position = request.form.get('job_position')
        emp.status = request.form.get('status', emp.status)
        
        db.session.commit()
        flash('Odeeffannoon hojjetaa milkaa\'inaan fooyya\'eera!', 'success')
        return redirect(url_for('employees'))

    all_branches = Branch.query.all()
    all_ranks = Rank.query.all()
    return render_template('edit_employee.html', employee=emp, branches=all_branches, ranks=all_ranks)

@app.route('/branches')
@login_required
def branches():
    all_branches = Branch.query.all()
    return render_template('branches.html', branches=all_branches)

# --- TRANSFER ROUTES ---

@app.route('/transfers')
@login_required
def transfers():
    if current_user.role == 'admin':
        all_transfers = Transfer.query.all()
    else:
        if hasattr(Transfer, 'from_branch_id') and current_user.branch_id:
            all_transfers = Transfer.query.filter_by(from_branch_id=current_user.branch_id).all()
        else:
            all_transfers = Transfer.query.all()
            
    all_employees = Employee.query.all() if current_user.role == 'admin' else Employee.query.filter_by(branch_id=current_user.branch_id).all()
    all_branches = Branch.query.all()
    return render_template('transfers.html', transfers=all_transfers, employees=all_employees, branches=all_branches)

@app.route('/add_transfer', methods=['POST'])
@login_required
def add_transfer():
    employee_id = request.form.get('employee_id')
    to_branch_id = request.form.get('to_branch_id')
    reason = request.form.get('reason')
    transfer_date_str = request.form.get('transfer_date')
    
    emp = Employee.query.get_or_404(employee_id)
    from_branch_id = emp.branch_id
    
    parsed_date = datetime.utcnow()
    if transfer_date_str:
        try:
            parsed_date = datetime.strptime(transfer_date_str, '%Y-%m-%d')
        except ValueError:
            pass
    
    transfer_data = {
        'employee_id': employee_id,
        'to_branch_id': to_branch_id,
        'reason': reason,
        'transfer_date': parsed_date,
        'status': 'Pending'
    }
    if hasattr(Transfer, 'from_branch_id'):
        transfer_data['from_branch_id'] = from_branch_id

    new_transfer = Transfer(**transfer_data)
    
    db.session.add(new_transfer)
    db.session.commit()
    flash('Gaaffiin jijjiirraa milkaa\'inaan dhiyaateera!', 'success')
    return redirect(url_for('transfers'))

@app.route('/update_transfer_status/<int:id>', methods=['POST'])
@admin_required
def update_transfer_status(id):
    tr = Transfer.query.get_or_404(id)
    status = request.form.get('status')
    approval_reason = request.form.get('approval_reason')
    
    tr.status = status
    if hasattr(tr, 'approval_reason'):
        tr.approval_reason = approval_reason
    
    if status == 'Approved' and tr.to_branch_id:
        emp = Employee.query.get(tr.employee_id)
        if emp:
            emp.branch_id = tr.to_branch_id
            
    db.session.commit()
    flash('Murteen jijjiirraa milkaa\'inaan galmaa\'eera!', 'success')
    return redirect(url_for('transfers'))

# ----------------------------------------------------

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
    branches = Branch.query.all()
    return render_template('settings.html', users=users, branches=branches)

@app.route('/add_user', methods=['POST'])
@admin_required
def add_user():
    username = request.form.get('username')
    password = request.form.get('password')
    role = request.form.get('role', 'user')
    branch_id = request.form.get('branch_id')
    
    existing_user = User.query.filter_by(username=username).first()
    if existing_user:
        flash('Maqaan fayyadamaa kun kanaan dura jira!', 'danger')
    else:
        hashed_pw = generate_password_hash(password)
        new_user = User(
            username=username, 
            password=hashed_pw, 
            role=role, 
            branch_id=int(branch_id) if branch_id else None
        )
        db.session.add(new_user)
        db.session.commit()
        flash('Fayyadamni haaraan damee isaa waliin milkaa\'inaan uumamee jira!', 'success')
        
    return redirect(url_for('settings'))

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

if __name__ == '__main__':
    app.run(debug=True)