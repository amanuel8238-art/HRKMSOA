import os
import io
import shutil
from datetime import datetime, date
from flask import Flask, render_template, redirect, url_for, request, flash, abort, send_file, jsonify
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, User, Employee, Branch, Rank, Transfer, DisciplineRecord
from sqlalchemy.exc import IntegrityError
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

# Function umrii herreequuf (Bara amma Jiru 2019 akka bu'uuraatti fayyadama) - Lakkoofsa qofa deebisa
def calculate_age(birth_date):
    if not birth_date:
        return "Hin beekamu"
    try:
        b_str = str(birth_date).strip().split()[0]
        b_year = None
        if '-' in b_str:
            parts = b_str.split('-')
            b_year = int(parts[0]) if len(parts[0]) == 4 else int(parts[2])
        elif '/' in b_str:
            parts = b_str.split('/')
            if len(parts) == 3:
                y = int(parts[2]) if len(parts[2]) == 4 else int(parts[0])
                if y < 100:
                    y += 1900 if y > 30 else 2000
                b_year = y
        elif b_str.isdigit() and len(b_str) == 4:
            b_year = int(b_str)
        
        if b_year:
            # Akka Lakkoobsa Itoophiyaatti bara amma jiru 2019 godhameera
            current_eth_year = 2019
            age = current_eth_year - b_year
            return age  # Jecha "Waggaa" jedhu dhiisee lakkoofsa qofa deebisa
    except Exception:
        pass
    return "Hin beekamu"

@app.context_processor
def utility_processor():
    def endpoint_exists(endpoint):
        try:
            url_for(endpoint)
            return True
        except Exception:
            return False
    return dict(endpoint_exists=endpoint_exists, calculate_age=calculate_age)

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
    
    import sqlalchemy as sa
    engine = db.engine
    inspector = sa.inspect(engine)
    if 'employee' in inspector.get_table_names():
        columns = [col['name'] for col in inspector.get_columns('employee')]
        with engine.begin() as conn:
            if 'pension_number' not in columns:
                conn.execute(sa.text("ALTER TABLE employee ADD COLUMN pension_number VARCHAR(100)"))
            if 'food_allowance' not in columns:
                conn.execute(sa.text("ALTER TABLE employee ADD COLUMN food_allowance FLOAT DEFAULT 0.0"))
            if 'responsibility_allowance' not in columns:
                conn.execute(sa.text("ALTER TABLE employee ADD COLUMN responsibility_allowance FLOAT DEFAULT 0.0"))
            if 'other_allowance' not in columns:
                conn.execute(sa.text("ALTER TABLE employee ADD COLUMN other_allowance FLOAT DEFAULT 0.0"))
            if 'perf_score' not in columns:
                conn.execute(sa.text("ALTER TABLE employee ADD COLUMN perf_score FLOAT DEFAULT 0.0"))
            if 'edu_score' not in columns:
                conn.execute(sa.text("ALTER TABLE employee ADD COLUMN edu_score FLOAT DEFAULT 0.0"))
            if 'discipline_score' not in columns:
                conn.execute(sa.text("ALTER TABLE employee ADD COLUMN discipline_score FLOAT DEFAULT 0.0"))
            if 'law_score' not in columns:
                conn.execute(sa.text("ALTER TABLE employee ADD COLUMN law_score FLOAT DEFAULT 0.0"))
            if 'experience_score' not in columns:
                conn.execute(sa.text("ALTER TABLE employee ADD COLUMN experience_score FLOAT DEFAULT 0.0"))
            if 'service_score' not in columns:
                conn.execute(sa.text("ALTER TABLE employee ADD COLUMN service_score FLOAT DEFAULT 0.0"))
            if 'total_score' not in columns:
                conn.execute(sa.text("ALTER TABLE employee ADD COLUMN total_score FLOAT DEFAULT 0.0"))
            if 'next_promotion_status' not in columns:
                conn.execute(sa.text("ALTER TABLE employee ADD COLUMN next_promotion_status VARCHAR(100)"))
            if 'next_promotion_date' not in columns:
                conn.execute(sa.text("ALTER TABLE employee ADD COLUMN next_promotion_date VARCHAR(50)"))

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
    current_eth_year = 2019
        
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
                    age = current_eth_year - birth_year
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
    ethiopian_today = (2019, 1, 28)

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

@app.route('/branches')
@login_required
def branches():
    all_branches = Branch.query.all()
    return render_template('branches.html', branches=all_branches)

@app.route('/transfers')
@login_required
def transfers():
    transfers_list = Transfer.query.filter(db.not_(Transfer.reason.ilike('%Gaaffii Gonfoo%'))).all()
    branches = Branch.query.all()
    
    user_b_val = int(current_user.branch_id) if current_user.branch_id and str(current_user.branch_id).isdigit() else current_user.branch_id
    if current_user.role == 'admin':
        employees = Employee.query.filter_by(status='Active').all()
    else:
        employees = Employee.query.filter_by(branch_id=user_b_val, status='Active').all() if user_b_val else []
        
    return render_template('transfers.html', transfers=transfers_list, employees=employees, branches=branches)

@app.route('/add_transfer', methods=['POST'])
@login_required
def add_transfer():
    try:
        create_local_backup()
        employee_id = request.form.get('employee_id')
        to_branch_id = request.form.get('to_branch_id')
        reason = request.form.get('reason')
        transfer_date = request.form.get('transfer_date') or "2019-01-28"

        emp = Employee.query.get(employee_id) if employee_id and str(employee_id).isdigit() else None
        from_b_id = emp.branch_id if emp else None

        new_transfer = Transfer(
            employee_id=int(employee_id) if employee_id and str(employee_id).isdigit() else None,
            from_branch_id=from_b_id,
            to_branch_id=int(to_branch_id) if to_branch_id and str(to_branch_id).isdigit() else to_branch_id,
            reason=reason,
            transfer_date=transfer_date,
            status='Pending'
        )
        db.session.add(new_transfer)
        db.session.commit()
        flash("Gaaffiin jijjiirraa milkaa'inaan galmaa'eera!", 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Dogoggorri uumameera: {str(e)}', 'danger')
    return redirect(url_for('transfers'))

@app.route('/update_transfer_status/<int:id>', methods=['POST'])
@login_required
@admin_required
def update_transfer_status(id):
    t_record = Transfer.query.get_or_404(id)
    try:
        create_local_backup()
        new_status = request.form.get('status')
        t_record.status = new_status
        t_record.approval_reason = request.form.get('approval_reason')
        
        if new_status == 'Approved' and t_record.employee_id and t_record.to_branch_id:
            emp = Employee.query.get(t_record.employee_id)
            if emp:
                emp.branch_id = t_record.to_branch_id
                
        db.session.commit()
        flash("Murteen jijjiirraa milkaa'inaan galmaa'eera, hojjetaanis gara damee haaraatti jijjiirameera!", 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Dogoggorri uumameera: {str(e)}', 'danger')
    return redirect(url_for('transfers'))

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
            emp.unique_id = request.form.get('unique_id') or None
            emp.pension_number = request.form.get('pension_number') or None
            emp.gender = request.form.get('gender')
            
            if current_user.role == 'admin':
                b_id = request.form.get('branch_id')
                if b_id:
                    emp.branch_id = int(b_id) if str(b_id).isdigit() else b_id

            rank_input = request.form.get('rank_id') or request.form.get('rank')
            if rank_input:
                emp.rank_id = resolve_rank_id(rank_input)

            emp.rank_date = request.form.get('rank_date') or emp.rank_date
            emp.hire_date = request.form.get('hire_date') or emp.hire_date
            emp.birth_date = request.form.get('birth_date') or emp.birth_date
            
            emp.rank_salary = float(request.form.get('rank_salary') or 0.0)
            emp.location_allowance = float(request.form.get('location_allowance') or 0.0)
            emp.food_allowance = float(request.form.get('food_allowance') or 0.0)
            emp.responsibility_allowance = float(request.form.get('responsibility_allowance') or 0.0)
            emp.other_allowance = float(request.form.get('other_allowance') or 0.0)
            
            emp.education_level = request.form.get('education_level') or emp.education_level
            emp.field_of_study = request.form.get('field_of_study') or emp.field_of_study
            emp.job_position = request.form.get('job_position') or emp.job_position

            db.session.commit()
            flash("Odeeffannoon hojjetaa milkaa'inaan fooyya'eera!", 'success')
            return redirect(url_for('employees'))
        except IntegrityError:
            db.session.rollback()
            flash("ID Addaa (Unique ID) kun duraanuu hojjetaa biraaf kennameera! Maaloo ID adda ta'e fayyadami.", 'danger')
        except Exception as e:
            db.session.rollback()
            flash(f'Dogoggorri uumameera: {str(e)}', 'danger')

    all_branches = Branch.query.all()
    all_ranks = Rank.query.all()
    return render_template('edit_employee.html', employee=emp, branches=all_branches, ranks=all_ranks)

@app.route('/delete_employee/<int:id>', methods=['POST'])
@login_required
@admin_required
def delete_employee(id):
    emp = Employee.query.get_or_404(id)
    try:
        create_local_backup()
        db.session.delete(emp)
        db.session.commit()
        flash("Hojjetaan milkaa'inaan haqameera!", 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Dogoggorri uumameera: {str(e)}', 'danger')
    return redirect(url_for('employees'))

@app.route('/update_rank_status/<int:id>', methods=['POST'])
@login_required
@admin_required
def update_rank_status(id):
    rank_rec = Rank.query.get_or_404(id)
    try:
        create_local_backup()
        new_name = request.form.get('name')
        new_desc = request.form.get('description')
        if new_name:
            rank_rec.name = new_name
        if new_desc is not None:
            rank_rec.description = new_desc
        db.session.commit()
        flash("Gulantaan (Rank) milkaa'inaan fooyya'eera!", 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Dogoggorri uumameera: {str(e)}', 'danger')
    return redirect(url_for('ranks'))

@app.route('/evaluate_employee/<int:id>', methods=['GET', 'POST'])
@login_required
def evaluate_employee(id):
    emp = Employee.query.get_or_404(id)
    user_b_val = int(current_user.branch_id) if current_user.branch_id and str(current_user.branch_id).isdigit() else current_user.branch_id
    if current_user.role != 'admin' and emp.branch_id != user_b_val:
        abort(403)

    if request.method == 'POST':
        try:
            create_local_backup()
            reason_text = request.form.get('reason', 'Gaaffii Gonfoo (Promotion Evaluation)')
            transfer_date = request.form.get('transfer_date') or "2019-01-28"

            new_promotion = Transfer(
                employee_id=emp.id,
                from_branch_id=emp.branch_id,
                to_branch_id=emp.branch_id,
                reason=f"Gaaffii Gonfoo: {reason_text}",
                transfer_date=transfer_date,
                status='Pending'
            )
            db.session.add(new_promotion)
            db.session.commit()
            flash("Madaalliin gonfoo milkaa'inaan galmaa'ee gara gaaffiiwwan gonfootti ergameera!", 'success')
            return redirect(url_for('promotions'))
        except Exception as e:
            db.session.rollback()
            flash(f'Dogoggorri uumameera: {str(e)}', 'danger')

    all_ranks = Rank.query.all()
    return render_template('evaluate_employee.html', employee=emp, ranks=all_ranks)

@app.route('/add_discipline/<int:employee_id>', methods=['GET', 'POST'])
@login_required
def add_discipline(employee_id):
    emp = Employee.query.get_or_404(employee_id)
    user_b_val = int(current_user.branch_id) if current_user.branch_id and str(current_user.branch_id).isdigit() else current_user.branch_id
    if current_user.role != 'admin' and emp.branch_id != user_b_val:
        abort(403)

    if request.method == 'POST':
        try:
            create_local_backup()
            penalty_type = request.form.get('penalty_type')
            description = request.form.get('description', '')
            d_date = request.form.get('date') or request.form.get('offense_date') or "2019-01-28"

            new_record = DisciplineRecord(
                employee_id=emp.id,
                penalty_type=penalty_type,
                description=description,
                date_given=d_date
            )
            db.session.add(new_record)
            db.session.commit()
            flash("Odeeffannoon naamusa hojjetaa milkaa'inaan galmaa'eera!", 'success')
            return redirect(url_for('employees'))
        except Exception as e:
            db.session.rollback()
            flash(f'Dogoggorri uumameera: {str(e)}', 'danger')

    return render_template('add_discipline.html', employee=emp)

@app.route('/warnings')
@login_required
def warnings():
    branch_id_filter = request.args.get('branch_id')
    
    query = DisciplineRecord.query.join(Employee, DisciplineRecord.employee_id == Employee.id).filter(
        DisciplineRecord.penalty_type.ilike('%akeekkachiisa%')
    )
    
    if current_user.role == 'admin':
        if branch_id_filter and str(branch_id_filter).isdigit():
            query = query.filter(Employee.branch_id == int(branch_id_filter))
    else:
        user_b = current_user.branch_id
        if user_b:
            b_val = int(user_b) if str(user_b).isdigit() else user_b
            query = query.filter(Employee.branch_id == b_val)
        else:
            query = query.filter(False)
            
    records = query.all()
    all_branches = Branch.query.all()
    return render_template('warnings.html', records=records, all_branches=all_branches, selected_branch=branch_id_filter)

@app.route('/penalties')
@login_required
def penalties():
    branch_id_filter = request.args.get('branch_id')
    
    query = DisciplineRecord.query.join(Employee, DisciplineRecord.employee_id == Employee.id).filter(
        db.not_(DisciplineRecord.penalty_type.ilike('%akeekkachiisa%'))
    )
    
    if current_user.role == 'admin':
        if branch_id_filter and str(branch_id_filter).isdigit():
            query = query.filter(Employee.branch_id == int(branch_id_filter))
    else:
        user_b = current_user.branch_id
        if user_b:
            b_val = int(user_b) if str(user_b).isdigit() else user_b
            query = query.filter(Employee.branch_id == b_val)
        else:
            query = query.filter(False)
            
    records = query.all()
    all_branches = Branch.query.all()
    return render_template('penalties.html', records=records, all_branches=all_branches, selected_branch=branch_id_filter)

@app.route('/disciplined_employees')
@login_required
def disciplined_employees():
    branch_id_filter = request.args.get('branch_id')
    
    query = Employee.query.join(DisciplineRecord, Employee.id == DisciplineRecord.employee_id).distinct()
    
    if current_user.role == 'admin':
        if branch_id_filter and str(branch_id_filter).isdigit():
            query = query.filter(Employee.branch_id == int(branch_id_filter))
    else:
        user_b = current_user.branch_id
        if user_b:
            b_val = int(user_b) if str(user_b).isdigit() else user_b
            query = query.filter(Employee.branch_id == b_val)
        else:
            query = query.filter(False)
            
    employees = query.all()
    all_branches = Branch.query.all()
    return render_template('disciplined_employees.html', employees=employees, all_branches=all_branches, selected_branch=branch_id_filter)

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

@app.route('/add_employee', methods=['POST'])
@login_required
def add_employee():
    full_name = request.form.get('full_name')
    u_id = request.form.get('unique_id')
    gender = request.form.get('gender')
    
    unique_id_val = u_id.strip() if u_id and u_id.strip() != '' else None

    if current_user.role == 'admin':
        branch_id = request.form.get('branch_id')
    else:
        branch_id = current_user.branch_id

    rank_input = request.form.get('rank_id') or request.form.get('rank')
    rank_id = resolve_rank_id(rank_input)

    if not full_name:
        flash("Maqaa guutuu hojjetaa galchuun dirqama!", "danger")
        return redirect(url_for('employees'))

    try:
        create_local_backup()
        new_emp = Employee(
            full_name=full_name,
            unique_id=unique_id_val,
            pension_number=request.form.get('pension_number') or None,
            gender=gender or 'Dhiira',
            branch_id=int(branch_id) if branch_id and str(branch_id).isdigit() else branch_id,
            rank_id=int(rank_id) if rank_id and str(rank_id).isdigit() else None,
            rank_date=request.form.get('rank_date') or None,
            hire_date=request.form.get('hire_date') or None,
            birth_date=request.form.get('birth_date') or None,
            rank_salary=float(request.form.get('rank_salary') or 0.0),
            location_allowance=float(request.form.get('location_allowance') or 0.0),
            food_allowance=float(request.form.get('food_allowance') or 0.0),
            responsibility_allowance=float(request.form.get('responsibility_allowance') or 0.0),
            other_allowance=float(request.form.get('other_allowance') or 0.0),
            education_level=request.form.get('education_level') or None,
            field_of_study=request.form.get('field_of_study') or None,
            job_position=request.form.get('job_position') or None,
            status='Active'
        )
        db.session.add(new_emp)
        db.session.commit()
        flash("Hojjetaan haaraan milkaa'inaan galmaa'eera!", 'success')
    except IntegrityError:
        db.session.rollback()
        flash("ID Addaa (Unique ID) kun duraanuu hojjetaa biraaf kennameera! Maaloo ID adda ta'e fayyadami.", 'danger')
    except Exception as e:
        db.session.rollback()
        flash(f'Dogoggorri uumameera: {str(e)}', 'danger')
        
    return redirect(url_for('employees'))

@app.route('/ranks')
@login_required
def ranks():
    all_ranks = Rank.query.all()
    return render_template('ranks.html', ranks=all_ranks)

@app.route('/export_ranks_excel')
@login_required
def export_ranks_excel():
    ranks_data = Rank.query.all()
    if not ranks_data:
        flash("Odeeffannoon ykn daataan gulantaalee (ranks) waan hin jirreef, Excel export gochuun hin danda'amu!", 'warning')
        return redirect(url_for('ranks'))

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
    return send_file(
        output, 
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', 
        as_attachment=True, 
        download_name='HRKMSO_Ranks_Report.xlsx'
    )

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
    if not emps:
        flash("Odeeffannoon ykn daataan hojjettootaa filatame waan hin jirreef, Excel export gochuun hin danda'amu!", 'warning')
        return redirect(url_for('employees'))

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
    return send_file(
        output, 
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', 
        as_attachment=True, 
        download_name='HRKMSO_Report.xlsx'
    )

@app.route('/promotions')
@login_required
def promotions():
    branch_id_filter = request.args.get('branch_id')
    status_filter = request.args.get('status', 'Pending') 
    all_branches = Branch.query.all()
    
    query = Transfer.query.filter(Transfer.reason.ilike('%Gaaffii Gonfoo%'))
    
    if status_filter and status_filter != 'All':
        query = query.filter_by(status=status_filter)

    if current_user.role == 'admin':
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
            branch_id_val = int(user_b) if str(user_b).isdigit() else user_b
            promotions_list = query.join(Employee, Transfer.employee_id == Employee.id).filter(
                Employee.branch_id == branch_id_val
            ).all()
        else:
            promotions_list = []

    return render_template(
        'promotions.html', 
        promotions=promotions_list, 
        all_branches=all_branches, 
        selected_branch=branch_id_filter,
        selected_status=status_filter
    )

@app.route('/approve_promotion/<int:id>', methods=['POST'])
@login_required
@admin_required
def approve_promotion(id):
    transfer_record = Transfer.query.get_or_404(id)
    try:
        create_local_backup()
        transfer_record.status = 'Approved'
        db.session.commit()
        flash("Gaaffiin gonfoo milkaa'inaan eeyyamameera (Approved)!", 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Dogoggorri uumameera: {str(e)}', 'danger')
    return redirect(url_for('promotions'))

@app.route('/reject_promotion/<int:id>', methods=['POST'])
@login_required
@admin_required
def reject_promotion(id):
    transfer_record = Transfer.query.get_or_404(id)
    try:
        create_local_backup()
        transfer_record.status = 'Rejected'
        db.session.commit()
        flash("Gaaffiin gonfoo dhorkameera (Rejected).", 'warning')
    except Exception as e:
        db.session.rollback()
        flash(f'Dogoggorri uumameera: {str(e)}', 'danger')
    return redirect(url_for('promotions'))

@app.route('/delete_promotion/<int:id>', methods=['POST'])
@login_required
@admin_required
def delete_promotion(id):
    transfer_record = Transfer.query.get_or_404(id)
    try:
        create_local_backup()
        db.session.delete(transfer_record)
        db.session.commit()
        flash("Gaaffiin gonfoo milkaa'inaan haqameera!", 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Dogoggorri uumameera: {str(e)}', 'danger')
    return redirect(url_for('promotions'))

@app.route('/export_promotions_excel')
@login_required
def export_promotions_excel():
    branch_id_filter = request.args.get('branch_id')
    status_filter = request.args.get('status', 'Pending')

    query = Transfer.query.filter(Transfer.reason.ilike('%Gaaffii Gonfoo%'))
    
    if status_filter and status_filter != 'All':
        query = query.filter_by(status=status_filter)

    if current_user.role == 'admin':
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
            branch_id_val = int(user_b) if str(user_b).isdigit() else user_b
            promotions_list = query.join(Employee, Transfer.employee_id == Employee.id).filter(
                Employee.branch_id == branch_id_val
            ).all()
        else:
            promotions_list = []

    if not promotions_list:
        flash("Odeeffannoon ykn daataan gaaffii gonfoo filatame waan hin jirreef, Excel export gochuun hin danda'amu!", 'warning')
        return redirect(url_for('promotions'))

    current_eth_year = 2019

    data = []
    for index, tr in enumerate(promotions_list, start=1):
        emp = tr.employee
        b_name = '-'
        if emp and emp.branch:
            b_name = emp.branch.name

        age = '-'
        if emp and emp.birth_date:
            try:
                b_str = str(emp.birth_date).strip().split()[0]
                b_year = None
                if '-' in b_str:
                    parts = b_str.split('-')
                    b_year = int(parts[0]) if len(parts[0]) == 4 else int(parts[2])
                elif '/' in b_str:
                    parts = b_str.split('/')
                    if len(parts) == 3:
                        y = int(parts[2]) if len(parts[2]) == 4 else int(parts[0])
                        if y < 100:
                            y += 1900 if y > 30 else 2000
                        b_year = y
                elif b_str.isdigit() and len(b_str) == 4:
                    b_year = int(b_str)
                
                if b_year:
                    age = current_eth_year - b_year
            except Exception:
                pass

        data.append({
            "Lak": index,
            "Gonfa Ammaa Qabu": emp.rank.name if emp and emp.rank else '-',
            "Maqaa Miseensotaa": emp.full_name if emp else '-',
            "Bakka Hojii": b_name,
            "Gahee Hojii": emp.job_position if emp and emp.job_position else '-',
            "Saala": emp.gender if emp and emp.gender else '-',
            "Umrii": age,
            "Bara Gonfaa Dura Yeroo Itti Argate": emp.rank_date if emp and emp.rank_date else '-',
            "Gonfaa Itti Aanu Yeroo Itti Argatu": emp.next_promotion_date if emp and emp.next_promotion_date else (str(tr.transfer_date) if tr.transfer_date else '-'),
            "Sadarkaa Barumsaa": emp.education_level if emp and emp.education_level else '-',
            "Gosa Barumsaa": emp.field_of_study if emp and emp.field_of_study else '-',
            "Bu'uura Raawwii Hojii (25%)": emp.perf_score if emp and emp.perf_score is not None else '0.00',
            "Sadarkaa Barumsaa (20%)": emp.edu_score if emp and emp.edu_score is not None else '0.00',
            "Naamusaa Poolisii (20%)": emp.discipline_score if emp and emp.discipline_score is not None else '0.00',
            "Seera fi Heera (10%)": emp.law_score if emp and emp.law_score is not None else '0.00',
            "Muxannoo Hojii (10%)": emp.experience_score if emp and emp.experience_score is not None else '0.00',
            "Mira Tajaajiltummaa (15%)": emp.service_score if emp and emp.service_score is not None else '0.00',
            "Ida'amaa": f"{emp.total_score}%" if emp and emp.total_score is not None else '0.00%',
            "Gonfoo Itti Guddatuu": emp.next_promotion_status if emp and emp.next_promotion_status else '-',
            "Haala (Status)": tr.status if tr.status else 'Pending'
        })
        
    df = pd.DataFrame(data)
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Promotions')
    output.seek(0)
    return send_file(
        output, 
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', 
        as_attachment=True, 
        download_name='Gaaffii_Gulantaa_Gonfoo.xlsx'
    )

if __name__ == '__main__':
    app.run(debug=True)