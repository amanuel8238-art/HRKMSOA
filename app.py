import os
import io
import shutil
from datetime import datetime, date
from flask import Flask, render_template, redirect, url_for, request, flash, abort, send_file, jsonify
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, User, Employee, Branch, Rank, Transfer, DisciplineRecord
from functools import wraps
import pandas as pd

# Guyyaa Itoophiyaatti jijjiiruuf (Safuu fi Error dhowwuuf try-except godhameera)
try:
    from py_ethiopian_date_converter import to_ethiopian, to_gregorian
except ImportError:
    def to_ethiopian(year, month, day):
        return year - 8, month, day
    def to_gregorian(year, month, day):
        return year + 8, month, day

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
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'admin':
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

# --- AUTOMATIC DATABASE BACKUP FUNCTION ---
def create_local_backup():
    try:
        db_path = os.path.join('instance', 'hrkmso.db')
        backup_dir = 'backups'
        
        if not os.path.exists(backup_dir):
            os.makedirs(backup_dir)
            
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_file = os.path.join(backup_dir, f'hrkmso_backup_{timestamp}.db')
        
        if os.path.exists(db_path):
            shutil.copy(db_path, backup_file)
            print(f"[MILKAA'E] Database backup ta'eera: {backup_file}")
    except Exception as e:
        print(f"[ERR] Backup godhuu irratti rakkoon uumame: {e}")

with app.app_context():
    db.create_all()
    
    # App-ichi yeroo ka'u automatic backup akka godhu
    create_local_backup()
    
    # 1. Admin Jalqabaa Uumuu
    if not User.query.filter_by(username='admin').first():
        hashed_pw = generate_password_hash('admin123')
        admin_user = User(username='admin', password=hashed_pw, role='admin', branch_id=None)
        db.session.add(admin_user)

    # 2. Sadarkaa (Rank) Jalqabaa akka hin dhabamne uumuu
    if not Rank.query.first():
        default_rank = Rank(name='Standard Rank', description='Default system rank')
        db.session.add(default_rank)

    # 3. Dameewwan 39an hunda ofumaan database keessatti galchuuf (Dadar corrected)
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

# --- HELPER FUNCTION FOR RETIRED AGE CALCULATION ---
def get_retired_employees_list(active_employees):
    today = date.today()
    retired_list = []
    for e in active_employees:
        if e.birth_date:
            try:
                b_str = str(e.birth_date).strip().split()[0]
                b_date = None
                
                if '-' in b_str:
                    parts = b_str.split('-')
                    if len(parts[0]) == 4:
                        b_date = date(int(parts[0]), int(parts[1]), int(parts[2]))
                    else:
                        b_date = date(int(parts[2]), int(parts[1]), int(parts[0]))
                elif '/' in b_str:
                    parts = b_str.split('/')
                    if len(parts) == 3:
                        year = int(parts[2]) if len(parts[2]) == 4 else int(parts[0])
                        month = int(parts[0]) if len(parts[2]) == 4 else int(parts[1])
                        day = int(parts[1]) if len(parts[2]) == 4 else int(parts[2])
                        if year < 100:
                            year += 1900 if year > 30 else 2000
                        b_date = date(year, month, day)
                
                if b_date:
                    age = today.year - b_date.year - ((today.month, today.day) < (b_date.month, b_date.day))
                    if age >= 55:
                        retired_list.append((e, age))
            except Exception:
                pass
    return retired_list

# --- ROUTES ---

@app.route('/')
@login_required
def dashboard():
    today = date.today()
    
    try:
        ethiopian_today = to_ethiopian(today.year, today.month, today.day)
    except Exception:
        ethiopian_today = None

    if current_user.role == 'admin':
        emp_count = Employee.query.filter_by(status='Active').count()
        branch_count = Branch.query.count()
        transfer_count = Transfer.query.count()
        
        male_count = Employee.query.filter_by(status='Active').filter(db.or_(Employee.gender == 'Dhiira', Employee.gender == 'Dhiirra')).count()
        female_count = Employee.query.filter_by(status='Active').filter(db.or_(Employee.gender == 'Dhalaa', Employee.gender == 'Dubartii')).count()
        
        inactive_statuses = ['Resigned', 'Terminated', "Du'aan", 'Fedhiitiin', 'Dhukkubaan', 'Dismissed']
        resigned_count = Employee.query.filter(Employee.status.in_(inactive_statuses)).count()
        
        all_emps = Employee.query.filter_by(status='Active').all()
    else:
        user_b = current_user.branch_id
        branch_id_val = int(user_b) if user_b and str(user_b).isdigit() else user_b
        emp_count = Employee.query.filter_by(branch_id=branch_id_val, status='Active').count() if user_b else 0
        branch_count = 1
        
        male_count = Employee.query.filter_by(branch_id=branch_id_val, status='Active').filter(db.or_(Employee.gender == 'Dhiira', Employee.gender == 'Dhiirra')).count() if user_b else 0
        female_count = Employee.query.filter_by(branch_id=branch_id_val, status='Active').filter(db.or_(Employee.gender == 'Dhalaa', Employee.gender == 'Dubartii')).count() if user_b else 0
        
        inactive_statuses = ['Resigned', 'Terminated', "Du'aan", 'Fedhiitiin', 'Dhukkubaan', 'Dismissed']
        resigned_count = Employee.query.filter_by(branch_id=branch_id_val).filter(Employee.status.in_(inactive_statuses)).count() if user_b else 0
        
        all_emps = Employee.query.filter_by(branch_id=branch_id_val, status='Active').all() if user_b else []

        if user_b:
            b_str = str(user_b)
            to_col = getattr(Transfer, 'to_branch_id', getattr(Transfer, 'to_branch', None))
            from_col = getattr(Transfer, 'from_branch_id', None)
            
            conditions = []
            if from_col is not None:
                conditions.append(db.cast(from_col, db.String) == b_str)
            if to_col is not None:
                conditions.append(db.cast(to_col, db.String) == b_str)
                
            transfer_count = Transfer.query.filter(db.or_(*conditions)).count() if conditions else 0
        else:
            transfer_count = 0

    retired_count = len(get_retired_employees_list(all_emps))

    warning_count = DisciplineRecord.query.filter(DisciplineRecord.penalty_type.ilike('%akeekkachiisa%')).count()
    penalty_count = DisciplineRecord.query.filter(db.not_(DisciplineRecord.penalty_type.ilike('%akeekkachiisa%'))).count()
    reward_count = 0 
    
    if hasattr(DisciplineRecord, 'with_disposing'):
        try:
            clean_count = emp_count - DisciplineRecord.query.with_disposing().count()
        except:
            clean_count = emp_count
    else:
        clean_count = emp_count

    return render_template('dashboard.html', 
                           emp_count=emp_count, 
                           branch_count=branch_count, 
                           transfer_count=transfer_count,
                           male_count=male_count,
                           female_count=female_count,
                           retired_count=retired_count,
                           resigned_count=resigned_count,
                           warning_count=warning_count,
                           penalty_count=penalty_count,
                           reward_count=reward_count,
                           clean_count=clean_count,
                           ethiopian_today=ethiopian_today)

@app.route('/retired_employees')
@login_required
def retired_employees():
    if current_user.role == 'admin':
        all_active = Employee.query.filter_by(status='Active').all()
    else:
        user_b = current_user.branch_id
        branch_id_val = int(user_b) if user_b and str(user_b).isdigit() else user_b
        all_active = Employee.query.filter_by(branch_id=branch_id_val, status='Active').all() if user_b else []
        
    retired_tuples = get_retired_employees_list(all_active)
    retired_list = [emp for emp, age in retired_tuples]
    return render_template('retired_employees.html', employees=retired_list)

@app.route('/resigned_employees')
@login_required
def resigned_employees():
    inactive_statuses = [
        'Resigned', 'Terminated', "Du'aan", 
        'Fedhiitiin', 'Dhukkubaan', 'Dismissed'
    ]
    query = Employee.query.filter(Employee.status.in_(inactive_statuses))
    
    if current_user.role != 'admin':
        user_b = current_user.branch_id
        branch_id_val = int(user_b) if user_b and str(user_b).isdigit() else user_b
        query = query.filter_by(branch_id=branch_id_val) if user_b else query.filter(False)
        
    resigned_list = query.all()
    return render_template('resigned_employees.html', employees=resigned_list)

@app.route('/employees')
@login_required
def employees():
    branch_id = request.args.get('branch_id')
    rank = request.args.get('rank')
    gender = request.args.get('gender')
    search_query = request.args.get('search', '')
    education_level = request.args.get('education_level', '')
    field_of_study = request.args.get('field_of_study', '')
    status_filter = request.args.get('status', 'Active')

    query = Employee.query

    if status_filter != 'All':
        query = query.filter_by(status=status_filter)

    if current_user.role != 'admin':
        branch_id = current_user.branch_id
        query = query.filter_by(branch_id=int(branch_id) if branch_id and str(branch_id).isdigit() else branch_id)
    elif branch_id:
        query = query.filter_by(branch_id=int(branch_id) if branch_id.isdigit() else branch_id)

    if rank:
        if str(rank).isdigit():
            query = query.join(Employee.rank).filter(db.or_(Rank.name == rank, Rank.id == int(rank)))
        else:
            query = query.join(Employee.rank).filter(Rank.name == rank)
    
    if gender:
        if gender in ['Dhalaa', 'Dubartii']:
            query = query.filter(db.or_(Employee.gender == 'Dhalaa', Employee.gender == 'Dubartii'))
        elif gender in ['Dhiira', 'Dhiirra']:
            query = query.filter(db.or_(Employee.gender == 'Dhiira', Employee.gender == 'Dhiirra'))
        else:
            query = query.filter_by(gender=gender)

    if education_level:
        query = query.filter(Employee.education_level.ilike(f'%{education_level}%'))

    if field_of_study:
        query = query.filter(Employee.field_of_study.ilike(f'%{field_of_study}%'))

    if search_query:
        query = query.filter(
            db.or_(
                Employee.full_name.ilike(f'%{search_query}%'),
                Employee.unique_id.ilike(f'%{search_query}%'),
                Employee.job_position.ilike(f'%{search_query}%')
            )
        )

    all_employees = query.all()
    
    if current_user.role == 'admin':
        all_branches = Branch.query.all()
    else:
        b_val = int(current_user.branch_id) if current_user.branch_id and str(current_user.branch_id).isdigit() else current_user.branch_id
        all_branches = Branch.query.filter_by(id=b_val).all()
        
    all_ranks = Rank.query.all()
    
    return render_template('employees.html', employees=all_employees, branches=all_branches, ranks=all_ranks)

@app.route('/export_employees_excel')
@login_required
def export_employees_excel():
    branch_id = request.args.get('branch_id')
    rank = request.args.get('rank')
    gender = request.args.get('gender')
    search_query = request.args.get('search', '')
    education_level = request.args.get('education_level', '')
    field_of_study = request.args.get('field_of_study', '')
    status_filter = request.args.get('status', 'Active')

    query = Employee.query
    if status_filter != 'All':
        query = query.filter_by(status=status_filter)

    if current_user.role != 'admin':
        branch_id = current_user.branch_id
        query = query.filter_by(branch_id=int(branch_id) if branch_id and str(branch_id).isdigit() else branch_id)
    elif branch_id:
        query = query.filter_by(branch_id=int(branch_id) if branch_id.isdigit() else branch_id)

    if rank:
        if str(rank).isdigit():
            query = query.join(Employee.rank).filter(db.or_(Rank.name == rank, Rank.id == int(rank)))
        else:
            query = query.join(Employee.rank).filter(Rank.name == rank)
    
    if gender:
        if gender in ['Dhalaa', 'Dubartii']:
            query = query.filter(db.or_(Employee.gender == 'Dhalaa', Employee.gender == 'Dubartii'))
        elif gender in ['Dhiira', 'Dhiirra']:
            query = query.filter(db.or_(Employee.gender == 'Dhiira', Employee.gender == 'Dhiirra'))
        else:
            query = query.filter_by(gender=gender)

    if education_level:
        query = query.filter(Employee.education_level.ilike(f'%{education_level}%'))

    if field_of_study:
        query = query.filter(Employee.field_of_study.ilike(f'%{field_of_study}%'))

    if search_query:
        query = query.filter(
            db.or_(
                Employee.full_name.ilike(f'%{search_query}%'),
                Employee.unique_id.ilike(f'%{search_query}%'),
                Employee.job_position.ilike(f'%{search_query}%')
            )
        )

    emps = query.all()
    data = []
    
    for idx, e in enumerate(emps, start=1):
        branch_name = e.branch.name if e.branch else 'N/A'
        rank_name = e.rank.name if e.rank else (e.rank_val if hasattr(e, 'rank_val') else 'N/A')
        
        data.append({
            'Lakk.': idx,
            'ID Addaa': e.unique_id if e.unique_id else '-',
            'Maqaa Guutuu': e.full_name,
            'Saala': e.gender if e.gender else '-',
            'Damee (Branch)': branch_name,
            'Gulantaa / Rank': rank_name,
            'Gita Hojii': e.job_position if e.job_position else '-',
            'Sadarkaa Barumsaa': e.education_level if e.education_level else '-',
            'Gosa Barumsaa': e.field_of_study if e.field_of_study else '-',
            'Guyyaa Qacarichaa': str(e.hire_date) if e.hire_date else '-',
            'Guyyaa Gulaantaa': str(e.rank_date) if e.rank_date else '-',
            'Guyyaa Dhalootaa': str(e.birth_date) if e.birth_date else '-',
            'Mindaa Gulaantaa': e.rank_salary if e.rank_salary else 0.0,
            'Mindaa Idoo': e.location_allowance if e.location_allowance else 0.0,
            'Durgoo Nyaataa': e.food_allowance if e.food_allowance else 0.0,
            'Status': e.status if e.status else '-',
            'Sababa Hojii Gadhiisuu': e.resignation_reason if hasattr(e, 'resignation_reason') and e.resignation_reason else '-'
        })
        
    df = pd.DataFrame(data)
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Miseensota Guutuu')
    output.seek(0)
    
    return send_file(
        output, 
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', 
        as_attachment=True, 
        download_name='HRKMSO_Miseensota_Report.xlsx'
    )

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

    rank_input = request.form.get('rank_id') or request.form.get('rank')
    rank_id = resolve_rank_id(rank_input)
    if not rank_id:
        first_rank = Rank.query.first()
        rank_id = first_rank.id if first_rank else None

    try:
        new_emp = Employee(
            full_name=full_name,
            unique_id=unique_id,
            gender=gender,
            branch_id=int(branch_id) if branch_id and str(branch_id).isdigit() else branch_id,
            rank_id=rank_id,
            rank_date=request.form.get('rank_date') or None,
            hire_date=request.form.get('hire_date') or None,
            birth_date=request.form.get('birth_date') or None,
            rank_salary=float(request.form.get('rank_salary') or 0.0),
            location_allowance=float(request.form.get('location_allowance') or 0.0),
            food_allowance=float(request.form.get('food_allowance') or 0.0),
            education_level=request.form.get('education_level'),
            field_of_study=request.form.get('field_of_study'),
            job_position=request.form.get('job_position'),
            status=request.form.get('status', 'Active')
        )
        db.session.add(new_emp)
        db.session.commit()
        flash('Hojjetaan haaraan milkaa’inaan galmaa’eera!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Dogoggorri uumameera (ID addaa wajjin walqabachuu danda’a): {str(e)}', 'danger')
        
    return redirect(url_for('employees'))

@app.route('/edit_employee/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_employee(id):
    emp = Employee.query.get_or_404(id)
    user_b_val = int(current_user.branch_id) if current_user.branch_id and str(current_user.branch_id).isdigit() else current_user.branch_id
    
    if current_user.role != 'admin' and emp.branch_id != user_b_val:
        abort(403)

    if request.method == 'POST':
        emp.full_name = request.form.get('full_name')
        emp.unique_id = request.form.get('unique_id')
        emp.gender = request.form.get('gender')
        
        if current_user.role == 'admin':
            branch_id = request.form.get('branch_id')
            emp.branch_id = int(branch_id) if branch_id and str(branch_id).isdigit() else branch_id

        rank_input = request.form.get('rank_id') or request.form.get('rank')
        if rank_input:
            resolved_rank_id = resolve_rank_id(rank_input)
            if resolved_rank_id:
                emp.rank_id = resolved_rank_id
        
        emp.rank_date = request.form.get('rank_date') or None
        emp.hire_date = request.form.get('hire_date') or None
        emp.birth_date = request.form.get('birth_date') or None
        
        emp.rank_salary = float(request.form.get('rank_salary') or 0.0)
        emp.location_allowance = float(request.form.get('location_allowance') or 0.0)
        emp.food_allowance = float(request.form.get('food_allowance') or 0.0)
        
        emp.education_level = request.form.get('education_level')
        emp.field_of_study = request.form.get('field_of_study')
        emp.job_position = request.form.get('job_position')
        
        new_status = request.form.get('status', emp.status)
        if new_status != emp.status and new_status in ['Resigned', 'Terminated', "Du'aan", 'Fedhiitiin', 'Dhukkubaan', 'Dismissed']:
            if hasattr(emp, 'resignation_reason'):
                emp.resignation_reason = request.form.get('resignation_reason')
            if hasattr(emp, 'resignation_date'):
                emp.resignation_date = datetime.utcnow()
        emp.status = new_status
        
        db.session.commit()
        flash('Odeeffannoon hojjetaa milkaa\'inaan fooyya\'eera!', 'success')
        return redirect(url_for('employees'))

    if current_user.role == 'admin':
        all_branches = Branch.query.all()
    else:
        all_branches = Branch.query.filter_by(id=user_b_val).all()
        
    all_ranks = Rank.query.all()
    return render_template('edit_employee.html', employee=emp, branches=all_branches, ranks=all_ranks)

@app.route('/branches')
@login_required
def branches():
    if current_user.role == 'admin':
        all_branches = Branch.query.all()
    else:
        b_val = int(current_user.branch_id) if current_user.branch_id and str(current_user.branch_id).isdigit() else current_user.branch_id
        all_branches = Branch.query.filter_by(id=b_val).all()
    return render_template('branches.html', branches=all_branches)

@app.route('/transfers')
@login_required
def transfers():
    if current_user.role == 'admin':
        all_transfers = Transfer.query.all()
    else:
        user_b = current_user.branch_id
        if user_b:
            b_str = str(user_b)
            to_col = getattr(Transfer, 'to_branch_id', getattr(Transfer, 'to_branch', None))
            from_col = getattr(Transfer, 'from_branch_id', None)
            
            conditions = []
            if from_col is not None:
                conditions.append(db.cast(from_col, db.String) == b_str)
            if to_col is not None:
                conditions.append(db.cast(to_col, db.String) == b_str)
                
            all_transfers = Transfer.query.filter(db.or_(*conditions)).all() if conditions else []
        else:
            all_transfers = []
            
    b_val = int(current_user.branch_id) if current_user.branch_id and str(current_user.branch_id).isdigit() else current_user.branch_id
    all_employees = Employee.query.filter_by(status='Active') if current_user.role == 'admin' else Employee.query.filter_by(branch_id=b_val, status='Active')
    all_employees = all_employees.all()
    all_branches = Branch.query.all()
        
    return render_template('transfers.html', transfers=all_transfers, employees=all_employees, branches=all_branches)

@app.route('/add_transfer', methods=['POST'])
@login_required
def add_transfer():
    employee_id = request.form.get('employee_id')
    to_branch_id = request.form.get('to_branch_id')
    reason = request.form.get('reason')
    transfer_date_str = request.form.get('transfer_date')
    
    emp = Employee.query.get_or_404(int(employee_id) if employee_id else 0)
    
    user_b_id = int(current_user.branch_id) if current_user.branch_id and str(current_user.branch_id).isdigit() else current_user.branch_id
    if current_user.role != 'admin' and emp.branch_id != user_b_id:
        abort(403)
        
    from_branch_id = emp.branch_id
    
    parsed_date = datetime.utcnow()
    if transfer_date_str:
        try:
            parsed_date = datetime.strptime(transfer_date_str, '%Y-%m-%d')
        except ValueError:
            pass
    
    transfer_data = {
        'employee_id': int(employee_id) if employee_id else None,
        'reason': reason,
        'transfer_date': parsed_date,
        'status': 'Pending'
    }
    
    if hasattr(Transfer, 'to_branch_id'):
        transfer_data['to_branch_id'] = int(to_branch_id) if to_branch_id and str(to_branch_id).isdigit() else to_branch_id
    elif hasattr(Transfer, 'to_branch'):
        transfer_data['to_branch'] = int(to_branch_id) if to_branch_id and str(to_branch_id).isdigit() else to_branch_id
        
    if hasattr(Transfer, 'from_branch_id'):
        transfer_data['from_branch_id'] = str(from_branch_id) if from_branch_id is not None else None

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
    
    target_branch = getattr(tr, 'to_branch_id', getattr(tr, 'to_branch', None))
    if status == 'Approved' and target_branch is not None:
        emp = Employee.query.get(tr.employee_id)
        if emp:
            if hasattr(tr, 'from_branch_id') and not tr.from_branch_id:
                tr.from_branch_id = emp.branch_id
            emp.branch_id = int(target_branch) if str(target_branch).isdigit() else target_branch
            
    db.session.commit()
    flash('Murteen jijjiirraa milkaa\'inaan galmaa\'eera!', 'success')
    return redirect(url_for('transfers'))

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

# --- KUTAA KALANDARII (CALENDAR ROUTES) ---
@app.route('/calendar')
@login_required
def calendar_view():
    return render_template('calendar.html')

@app.route('/api/calendar-events')
@login_required
def calendar_events():
    employees = Employee.query.all()
    events = []
    
    for emp in employees:
        if emp.hire_date:
            try:
                hire_str = str(emp.hire_date).split()[0]
                events.append({
                    'title': f"Qacaramuu: {emp.full_name}",
                    'start': hire_str,
                    'color': '#28a745'
                })
            except:
                pass
                
        if emp.birth_date:
            try:
                birth_str = str(emp.birth_date).split()[0]
                events.append({
                    'title': f"Dhalootaa: {emp.full_name}",
                    'start': birth_str,
                    'color': '#17a2b8'
                })
            except:
                pass
            
    return jsonify(events)

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
            branch_id=int(branch_id) if branch_id and str(branch_id).isdigit() else branch_id
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

# --- KUTAA GALMEE BADII NAAMUSAA (Discipline Records) ---
@app.route('/add_discipline/<int:employee_id>', methods=['GET', 'POST'])
@login_required
def add_discipline(employee_id):
    employee = Employee.query.get_or_404(employee_id)
    
    if request.method == 'POST':
        try:
            new_record = DisciplineRecord(
                employee_id=employee_id,
                offense_date=datetime.strptime(request.form['offense_date'], '%Y-%m-%d').date() if request.form.get('offense_date') else None,
                reporting_date=datetime.strptime(request.form['reporting_date'], '%Y-%m-%d').date() if request.form.get('reporting_date') else None,
                decision_date=datetime.strptime(request.form['decision_date'], '%Y-%m-%d').date() if request.form.get('decision_date') else None,
                effective_date=datetime.strptime(request.form['effective_date'], '%Y-%m-%d').date() if request.form.get('effective_date') else datetime.utcnow().date(),
                expiry_date=datetime.strptime(request.form['expiry_date'], '%Y-%m-%d').date() if request.form.get('expiry_date') else None,
                offense_type=request.form.get('offense_type'),
                penalty_type=request.form.get('penalty_type'),
                description=request.form.get('description'),
                evidence_details=request.form.get('evidence_details')
            )
            db.session.add(new_record)
            db.session.commit()
            flash('Galmeen naamusaa milkaa\'inaan galmaa\'eera!', 'success')
            return redirect(url_for('employees'))
        except Exception as e:
            db.session.rollback()
            flash(f'Dogoggorri uumameera: {str(e)}', 'danger')
            
    return render_template('add_discipline.html', employee=employee)

if __name__ == '__main__':
    app.run(debug=True)