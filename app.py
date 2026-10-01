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

try:
    from py_ethiopian_date_converter import to_ethiopian, to_gregorian
except ImportError:
    def to_ethiopian(year, month, day):
        return year - 8, month, day
    def to_gregorian(year, month, day):
        return year + 8, month, day

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'hrkmso-secret-key-2026')

@app.context_processor
def utility_processor():
    def endpoint_exists(endpoint):
        try:
            url_for(endpoint)
            return True
        except Exception:
            return False
    return dict(endpoint_exists=endpoint_exists)

instance_dir = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'instance')
if not os.path.exists(instance_dir):
    os.makedirs(instance_dir)

app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', f'sqlite:///{os.path.join(instance_dir, "hrkmso.db")}')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'admin':
            abort(403)
        return f(*args, **kwargs)
    return decorated_function

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

def create_local_backup():
    try:
        db_path = os.path.join(instance_dir, 'hrkmso.db')
        backup_dir = 'backups'
        if not os.path.exists(backup_dir):
            os.makedirs(backup_dir)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_file = os.path.join(backup_dir, f'hrkmso_backup_{timestamp}.db')
        if os.path.exists(db_path):
            shutil.copy(db_path, backup_file)
    except Exception as e:
        print(f"[ERR] Backup error: {e}")

with app.app_context():
    db.create_all()
    create_local_backup()
    
    if not User.query.filter_by(username='admin').first():
        hashed_pw = generate_password_hash('admin123')
        admin_user = User(username='admin', password=hashed_pw, role='admin', branch_id=None)
        db.session.add(admin_user)

    if not Rank.query.first():
        default_rank = Rank(name='Standard Rank', description='Default system rank')
        db.session.add(default_rank)

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

def get_retired_employees_list(active_employees):
    retired_list = []
    current_year = datetime.now().year
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
                    birth_year = b_date.year
                    age = current_year - birth_year
                    if age >= 55:
                        retired_list.append((e, age))
            except Exception:
                pass
    return retired_list

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            flash("Milkaa'inaan seenteetta!", 'success')
            next_page = request.args.get('next')
            return redirect(next_page or url_for('dashboard'))
        else:
            flash('Maqaa fayyadamaa ykn jecha iccitii dogoggortee jirta.', 'danger')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash("Milkaa'inaan baateetta!", 'info')
    return redirect(url_for('login'))

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
        transfer_count = Transfer.query.filter(db.not_(Transfer.reason.ilike('%Gaaffii Gonfoo%'))).count()
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
            branch_transfers = Transfer.query.filter(db.or_(*conditions)).all() if conditions else []
            transfer_count = len([t for t in branch_transfers if not (t.reason and "Gaaffii Gonfoo" in t.reason)])
        else:
            transfer_count = 0

    retired_count = len(get_retired_employees_list(all_emps))
    warning_count = DisciplineRecord.query.filter(DisciplineRecord.penalty_type.ilike('%akeekkachiisa%')).count()
    penalty_count = DisciplineRecord.query.filter(db.not_(DisciplineRecord.penalty_type.ilike('%akeekkachiisa%'))).count()
    
    if current_user.role == 'admin':
        promotion_count = Transfer.query.filter(Transfer.reason.ilike('%Gaaffii Gonfoo%')).count()
    else:
        promotion_count = Transfer.query.join(Employee, Transfer.employee_id == Employee.id).filter(
            Employee.branch_id == branch_id_val,
            Transfer.reason.ilike('%Gaaffii Gonfoo%')
        ).count() if user_b else 0

    reward_count = promotion_count
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
    retired_list = get_retired_employees_list(all_active)
    return render_template('retired_employees.html', retired_list=retired_list)

@app.route('/resigned_employees')
@login_required
def resigned_employees():
    inactive_statuses = ['Resigned', 'Terminated', "Du'aan", 'Fedhiitiin', 'Dhukkubaan', 'Dismissed']
    query = Employee.query.filter(Employee.status.in_(inactive_statuses))
    if current_user.role != 'admin':
        user_b = current_user.branch_id
        branch_id_val = int(user_b) if user_b and str(user_b).isdigit() else user_b
        query = query.filter_by(branch_id=branch_id_val) if user_b else query.filter(False)
    resigned_list = query.all()
    return render_template('resigned_employees.html', employees=resigned_list)

@app.route('/activate_employee/<int:id>', methods=['POST'])
@login_required
def activate_employee(id):
    emp = Employee.query.get_or_404(id)
    user_b_val = int(current_user.branch_id) if current_user.branch_id and str(current_user.branch_id).isdigit() else current_user.branch_id
    if current_user.role != 'admin' and emp.branch_id != user_b_val:
        abort(403)
    try:
        create_local_backup()
        emp.status = 'Active'
        if hasattr(emp, 'resignation_reason'):
            emp.resignation_reason = None
        if hasattr(emp, 'resignation_date'):
            emp.resignation_date = None
        db.session.commit()
        flash(f'Hojjetaan {emp.full_name} ammaa jalqabee deebi\'ee gara "Active"tti galfameera!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Dogoggorri uumameera: {str(e)}', 'danger')
    return redirect(request.referrer or url_for('employees'))

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
    sort_order = request.args.get('sort', 'az')

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

    if sort_order == 'za':
        query = query.order_by(Employee.full_name.desc())
    else:
        query = query.order_by(Employee.full_name.asc())

    all_employees = query.all()
    if current_user.role == 'admin':
        all_branches = Branch.query.all()
    else:
        b_val = int(current_user.branch_id) if current_user.branch_id and str(current_user.branch_id).isdigit() else current_user.branch_id
        all_branches = Branch.query.filter_by(id=b_val).all()
        
    all_ranks = Rank.query.all()
    return render_template('employees.html', employees=all_employees, branches=all_branches, ranks=all_ranks)

@app.route('/ranks')
@login_required
def ranks():
    all_ranks = Rank.query.all()
    return render_template('ranks.html', ranks=all_ranks)

@app.route('/export_ranks_excel')
@login_required
def export_ranks_excel():
    ranks_data = Rank.query.all()
    data = []
    for idx, r in enumerate(ranks_data, start=1):
        data.append({
            'Lakk.': idx,
            'Maqaa Gulantaa (Rank)': r.name,
            'Ibsaa': r.description if hasattr(r, 'description') and r.description else '-'
        })
        
    df = pd.DataFrame(data)
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Gulantaalee')
    output.seek(0)
    return send_file(output, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', as_attachment=True, download_name='HRKMSO_Ranks_Report.xlsx')

@app.route('/export_employees_excel')
@login_required
def export_employees_excel():
    branch_id = request.args.get('branch_id')
    search_query = request.args.get('search', '')
    status_filter = request.args.get('status', 'Active')

    query = Employee.query
    if status_filter != 'All':
        query = query.filter_by(status=status_filter)

    if current_user.role != 'admin':
        branch_id = current_user.branch_id
        query = query.filter_by(branch_id=int(branch_id) if branch_id and str(branch_id).isdigit() else branch_id)
    elif branch_id:
        query = query.filter_by(branch_id=int(branch_id) if branch_id.isdigit() else branch_id)

    if search_query:
        query = query.filter(Employee.full_name.ilike(f'%{search_query}%'))

    emps = query.all()
    data = []
    for idx, e in enumerate(emps, start=1):
        branch_name = e.branch.name if e.branch else 'N/A'
        rank_name = e.rank.name if e.rank else 'N/A'
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
            'Status': e.status if e.status else '-'
        })
        
    df = pd.DataFrame(data)
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Miseensota')
    output.seek(0)
    return send_file(output, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', as_attachment=True, download_name='HRKMSO_Report.xlsx')

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

    try:
        create_local_backup()
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
        flash("Hojjetaan haaraan milkaa’inaan galmaa’eera!", 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Dogoggorri uumameera: {str(e)}', 'danger')
    return redirect(url_for('employees'))

@app.route('/edit_employee/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_employee(id):
    emp = Employee.query.get_or_404(id)
    user_b_val = int(current_user.branch_id) if current_user.branch_id and str(current_user.branch_id).isdigit() else current_user.branch_id
    if current_user.role != 'admin' and emp.branch_id != user_b_val:
        abort(403)

    if request.method == 'POST':
        try:
            create_local_backup()
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
            emp.status = request.form.get('status', emp.status)
            
            db.session.commit()
            flash("Odeeffannoon hojjetaa milkaa\'inaan fooyya\'eera!", 'success')
            return redirect(url_for('employees'))
        except Exception as e:
            db.session.rollback()
            flash(f'Dogoggorri uumameera: {str(e)}', 'danger')

    all_branches = Branch.query.all() if current_user.role == 'admin' else Branch.query.filter_by(id=user_b_val).all()
    all_ranks = Rank.query.all()
    return render_template('edit_employee.html', employee=emp, branches=all_branches, ranks=all_ranks)

@app.route('/evaluate_employee/<int:id>', methods=['GET', 'POST'])
@login_required
def evaluate_employee(id):
    emp = Employee.query.get_or_404(id)
    user_b_val = int(current_user.branch_id) if current_user.branch_id and str(current_user.branch_id).isdigit() else current_user.branch_id
    if current_user.role != 'admin' and emp.branch_id != user_b_val:
        abort(403)

    all_ranks = Rank.query.all()
    if request.method == 'POST':
        try:
            perf = float(request.form.get('performance_score') or 0.0)
            edu = float(request.form.get('education_score') or 0.0)
            disc = float(request.form.get('discipline_score') or 0.0)
            law = float(request.form.get('law_score') or request.form.get('law_compliance_score') or 0.0)
            exp = float(request.form.get('experience_score') or 0.0)
            age = float(request.form.get('age_score') or 0.0)
            serv = float(request.form.get('service_delivery_score') or request.form.get('service_spirit_score') or 0.0)
            
            total_score = perf + edu + disc + law + exp + age + serv
            next_promotion_status = request.form.get('next_promotion_status')
            next_promotion_date = request.form.get('next_promotion_date')
            
            emp.total_score = total_score
            emp.next_promotion_status = next_promotion_status
            emp.next_promotion_date = next_promotion_date

            transfer_data = {
                'employee_id': emp.id,
                'reason': f"Gaaffii Gonfoo (Promotion Evaluation) - Qabxii Ida'amaa: {total_score:.2f}%, Sadarkaa Itti Aanu (Rank): {next_promotion_status}",
                'transfer_date': datetime.utcnow(),
                'status': 'Pending'
            }
            if hasattr(Transfer, 'to_branch_id'):
                transfer_data['to_branch_id'] = emp.branch_id
            if hasattr(Transfer, 'from_branch_id'):
                transfer_data['from_branch_id'] = str(emp.branch_id) if emp.branch_id is not None else None

            create_local_backup()
            new_transfer = Transfer(**transfer_data)
            db.session.add(new_transfer)
            db.session.commit()
            
            flash(f"Madaalliin hojjetaa {emp.full_name} milkaa\'inaan guutamee Gaaffii Gulantaa Gonfoo (Promotions) jalatti Head Office-tti ergameera!", 'success')
            return redirect(url_for('employees'))
        except Exception as e:
            db.session.rollback()
            flash(f'Herrega qabxii irratti dogoggorri uumameera: {str(e)}', 'danger')

    return render_template('evaluate_employee.html', employee=emp, ranks=all_ranks)

@app.route('/delete_employee/<int:id>', methods=['POST'])
@login_required
def delete_employee(id):
    emp = Employee.query.get_or_404(id)
    user_b_val = int(current_user.branch_id) if current_user.branch_id and str(current_user.branch_id).isdigit() else current_user.branch_id
    if current_user.role != 'admin' and emp.branch_id != user_b_val:
        abort(403)
        
    try:
        create_local_backup()
        db.session.delete(emp)
        db.session.commit()
        flash(f"Hojjetaan {emp.full_name} milkaa\'inaan haqameera!", 'success')
    except Exception as e:
        db.session.rollback()
        flash(f"Hojjetaan kun walitti dhufeenya table biroo qabaachuu danda\'a: {str(e)}", 'danger')
        
    return redirect(url_for('employees'))

@app.route('/employee/<int:employee_id>/discipline/add', methods=['GET', 'POST'])
@login_required
def add_discipline(employee_id):
    emp = Employee.query.get_or_404(employee_id)
    user_b_val = int(current_user.branch_id) if current_user.branch_id and str(current_user.branch_id).isdigit() else current_user.branch_id
    if current_user.role != 'admin' and emp.branch_id != user_b_val:
        abort(403)

    if request.method == 'POST':
        try:
            create_local_backup()
            new_record = DisciplineRecord(
                employee_id=emp.id,
                penalty_type=request.form.get('penalty_type'),
                reason=request.form.get('reason'),
                date_given=request.form.get('date_given') or date.today()
            )
            db.session.add(new_record)
            db.session.commit()
            flash("Galmeen namusaa/adabbii milkaa\'inaan galmaa\'eera!", 'success')
            return redirect(url_for('employees'))
        except Exception as e:
            db.session.rollback()
            flash(f'Dogoggorri uumameera: {str(e)}', 'danger')
        
    return render_template('add_discipline.html', employee=emp)

@app.route('/branches')
@login_required
def branches():
    if current_user.role == 'admin':
        all_branches = Branch.query.all()
    else:
        b_val = int(current_user.branch_id) if current_user.branch_id and str(current_user.branch_id).isdigit() else current_user.branch_id
        all_branches = Branch.query.filter_by(id=b_val).all()
    return render_template('branches.html', branches=all_branches)

# 1. Gaaffii Gulantaa Gonfoo (Promotions / Ranks) Qofaaf - Dameewwan 39 cufaaf filtering sirrii ta'e
@app.route('/promotions')
@login_required
def promotions():
    branch_id_filter = request.args.get('branch_id')
    all_branches = Branch.query.all()
    
    if current_user.role == 'admin':
        query = Transfer.query.filter(Transfer.reason.ilike('%Gaaffii Gonfoo%'))
        if branch_id_filter and str(branch_id_filter).isdigit():
            b_id_int = int(branch_id_filter)
            query = query.join(Employee, Transfer.employee_id == Employee.id).filter(
                db.or_(
                    Employee.branch_id == b_id_int,
                    Transfer.to_branch_id == b_id_int
                )
            )
        promotions_list = query.all()
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
            branch_transfers = Transfer.query.filter(db.or_(*conditions)).all() if conditions else []
            promotions_list = [t for t in branch_transfers if t.reason and "Gaaffii Gonfoo" in t.reason]
        else:
            promotions_list = []

    b_val = int(current_user.branch_id) if current_user.branch_id and str(current_user.branch_id).isdigit() else current_user.branch_id
    all_employees = Employee.query.filter_by(status='Active') if current_user.role == 'admin' else Employee.query.filter_by(branch_id=b_val, status='Active')
    all_employees = all_employees.all()
    
    return render_template('promotions.html', 
                           promotions=promotions_list,
                           promotions_count=len(promotions_list),
                           employees=all_employees, 
                           all_branches=all_branches, 
                           branches=all_branches,
                           selected_branch=branch_id_filter)

# 2. Gaaffii Jijjiirraa (Transfers) Qofaaf (Gonfoo Hin Qabanne)
@app.route('/transfers')
@login_required
def transfers():
    branch_id_filter = request.args.get('branch_id')
    all_branches = Branch.query.all()
    
    if current_user.role == 'admin':
        query = Transfer.query.filter(db.not_(Transfer.reason.ilike('%Gaaffii Gonfoo%')))
        if branch_id_filter and str(branch_id_filter).isdigit():
            b_id_int = int(branch_id_filter)
            query = query.join(Employee, Transfer.employee_id == Employee.id).filter(
                db.or_(
                    Employee.branch_id == b_id_int,
                    Transfer.to_branch_id == b_id_int
                )
            )
        all_transfers = query.all()
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
            branch_transfers = Transfer.query.filter(db.or_(*conditions)).all() if conditions else []
            all_transfers = [t for t in branch_transfers if not (t.reason and "Gaaffii Gonfoo" in t.reason)]
        else:
            all_transfers = []

    b_val = int(current_user.branch_id) if current_user.branch_id and str(current_user.branch_id).isdigit() else current_user.branch_id
    all_employees = Employee.query.filter_by(status='Active') if current_user.role == 'admin' else Employee.query.filter_by(branch_id=b_val, status='Active')
    all_employees = all_employees.all()
    
    return render_template('transfers.html', 
                           transfers=all_transfers,
                           transfers_count=len(all_transfers),
                           employees=all_employees, 
                           all_branches=all_branches,
                           branches=all_branches, 
                           selected_branch=branch_id_filter)

@app.route('/add_transfer', methods=['POST'])
@login_required
def add_transfer():
    employee_id = request.form.get('employee_id')
    to_branch_id = request.form.get('to_branch_id')
    reason = request.form.get('reason')
    
    emp = Employee.query.get_or_404(int(employee_id) if employee_id else 0)
    user_b_id = int(current_user.branch_id) if current_user.branch_id and str(current_user.branch_id).isdigit() else current_user.branch_id
    if current_user.role != 'admin' and emp.branch_id != user_b_id:
        abort(403)
        
    transfer_data = {
        'employee_id': int(employee_id) if employee_id else None,
        'reason': reason,
        'transfer_date': datetime.utcnow(),
        'status': 'Pending'
    }
    if hasattr(Transfer, 'to_branch_id'):
        transfer_data['to_branch_id'] = int(to_branch_id) if to_branch_id and str(to_branch_id).isdigit() else to_branch_id
    if hasattr(Transfer, 'from_branch_id'):
        transfer_data['from_branch_id'] = str(emp.branch_id) if emp.branch_id is not None else None

    try:
        create_local_backup()
        new_transfer = Transfer(**transfer_data)
        db.session.add(new_transfer)
        db.session.commit()
        flash("Gaaffiin jijjiirraa milkaa\'inaan dhiyaateera!", 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Dogoggorri uumameera: {str(e)}', 'danger')
        
    return redirect(url_for('transfers'))

@app.route('/update_transfer_status/<int:id>', methods=['POST'])
@admin_required
def update_transfer_status(id):
    tr = Transfer.query.get_or_404(id)
    status = request.form.get('status')
    tr.status = status
    
    try:
        create_local_backup()
        db.session.commit()
        flash("Haalli jijjiirraa/gonfoo milkaa'inaan haaromfameera!", 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Dogoggorri uumameera: {str(e)}', 'danger')
    
    if tr.reason and "Gaaffii Gonfoo" in tr.reason:
        return redirect(url_for('promotions'))
    return redirect(url_for('transfers'))

@app.route('/update_rank_status/<int:id>', methods=['POST'])
@admin_required
def update_rank_status(id):
    r = Rank.query.get_or_404(id)
    try:
        create_local_backup()
        r.name = request.form.get('name', r.name)
        r.description = request.form.get('description', r.description)
        db.session.commit()
        flash("Gulantaan (Rank) milkaa'inaan haaromfameera!", 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Dogoggorri uumameera: {str(e)}', 'danger')
    return redirect(url_for('ranks'))

if __name__ == '__main__':
    app.run(debug=True)