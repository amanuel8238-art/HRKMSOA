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
            current_eth_year = 2019
            age = current_eth_year - b_year
            return age
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
            if 'phone_number' not in columns:
                conn.execute(sa.text("ALTER TABLE employee ADD COLUMN phone_number VARCHAR(50)"))
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
            if 'last_promotion_date' not in columns:
                conn.execute(sa.text("ALTER TABLE employee ADD COLUMN last_promotion_date VARCHAR(50)"))

    if 'discipline_record' in inspector.get_table_names():
        disc_columns = [col['name'] for col in inspector.get_columns('discipline_record')]
        with engine.begin() as conn:
            if 'description' not in disc_columns:
                conn.execute(sa.text("ALTER TABLE discipline_record ADD COLUMN description TEXT"))
            if 'local_committee_date' not in disc_columns:
                conn.execute(sa.text("ALTER TABLE discipline_record ADD COLUMN local_committee_date VARCHAR(50)"))
            if 'zone_committee_date' not in disc_columns:
                conn.execute(sa.text("ALTER TABLE discipline_record ADD COLUMN zone_committee_date VARCHAR(50)"))
            if 'commission_sent_date' not in disc_columns:
                conn.execute(sa.text("ALTER TABLE discipline_record ADD COLUMN commission_sent_date VARCHAR(50)"))
            if 'discipline_status' not in disc_columns:
                conn.execute(sa.text("ALTER TABLE discipline_record ADD COLUMN discipline_status VARCHAR(100) DEFAULT 'mana_sirreessaa'"))
            if 'final_decision' not in disc_columns:
                conn.execute(sa.text("ALTER TABLE discipline_record ADD COLUMN final_decision TEXT"))

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
    branches = Branch.query.all()

    if current_user.role == 'admin':
        emp_count = Employee.query.filter_by(status='Active').count()
        branch_count = Branch.query.count()
        transfer_count = Transfer.query.filter(db.not_(Transfer.reason.ilike('%Gaaffii Gonfoo%'))).count()
        male_count = Employee.query.filter_by(status='Active').filter(db.or_(Employee.gender == 'Dhiira', Employee.gender == 'Dhiirra')).count()
        female_count = Employee.query.filter_by(status='Active').filter(db.or_(Employee.gender == 'Dhalaa', Employee.gender == 'Dubartii')).count()
        inactive_statuses = ['Resigned', 'Terminated', "Du'aan", 'Fedhiitiin', 'Dhukkubaan', 'Dismissed']
        resigned_count = Employee.query.filter(Employee.status.in_(inactive_statuses)).count()
        all_emps = Employee.query.filter_by(status='Active').all()
        
        local_committee_count = DisciplineRecord.query.filter(db.or_(DisciplineRecord.discipline_status == 'mana_sirreessaa', DisciplineRecord.discipline_status == None)).count()
        zone_committee_count = DisciplineRecord.query.filter_by(discipline_status='godinaa').count()
        commission_pending_count = DisciplineRecord.query.filter_by(discipline_status='komishinii').count()
        final_decided_count = DisciplineRecord.query.filter_by(discipline_status='murtaae').count()
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
            
            local_committee_count = DisciplineRecord.query.join(Employee).filter(Employee.branch_id == branch_id_val, db.or_(DisciplineRecord.discipline_status == 'mana_sirreessaa', DisciplineRecord.discipline_status == None)).count()
            zone_committee_count = DisciplineRecord.query.join(Employee).filter(Employee.branch_id == branch_id_val, DisciplineRecord.discipline_status == 'godinaa').count()
            commission_pending_count = DisciplineRecord.query.join(Employee).filter(Employee.branch_id == branch_id_val, DisciplineRecord.discipline_status == 'komishinii').count()
            final_decided_count = DisciplineRecord.query.join(Employee).filter(Employee.branch_id == branch_id_val, DisciplineRecord.discipline_status == 'murtaae').count()
        else:
            transfer_count = 0
            local_committee_count = zone_committee_count = commission_pending_count = final_decided_count = 0

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
                           branches=branches,
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
                           local_committee_count=local_committee_count,
                           zone_committee_count=zone_committee_count,
                           commission_pending_count=commission_pending_count,
                           final_decided_count=final_decided_count,
                           ethiopian_today=ethiopian_today)

@app.route('/api/dashboard-stats/<branch_id>')
@login_required
def get_branch_stats(branch_id):
    if branch_id == 'all':
        emp_query = Employee.query.filter_by(status='Active')
        all_active_for_retired = emp_query.all()
        promo_query = Transfer.query.filter(Transfer.reason.ilike('%Gaaffii Gonfoo%'))
        trans_query = Transfer.query.filter(db.not_(Transfer.reason.ilike('%Gaaffii Gonfoo%')))
        warning_query = DisciplineRecord.query.filter(DisciplineRecord.penalty_type.ilike('%akeekkachiisa%'))
        penalty_query = DisciplineRecord.query.filter(db.not_(DisciplineRecord.penalty_type.ilike('%akeekkachiisa%')))
        
        local_committee = DisciplineRecord.query.filter(db.or_(DisciplineRecord.discipline_status == 'mana_sirreessaa', DisciplineRecord.discipline_status == None)).count()
        zone_committee = DisciplineRecord.query.filter_by(discipline_status='godinaa').count()
        commission_pending = DisciplineRecord.query.filter_by(discipline_status='komishinii').count()
        final_decided = DisciplineRecord.query.filter_by(discipline_status='murtaae').count()
    else:
        b_id_str = str(branch_id)
        
        emp_query = Employee.query.filter(db.cast(Employee.branch_id, db.String) == b_id_str, Employee.status == 'Active')
        all_active_for_retired = emp_query.all()
        
        promo_query = Transfer.query.join(Employee, Transfer.employee_id == Employee.id).filter(
            db.cast(Employee.branch_id, db.String) == b_id_str,
            Transfer.reason.ilike('%Gaaffii Gonfoo%')
        )
        
        trans_query = Transfer.query.filter(
            db.or_(
                db.cast(Transfer.from_branch_id, db.String) == b_id_str,
                db.cast(Transfer.to_branch_id, db.String) == b_id_str
            ),
            db.not_(Transfer.reason.ilike('%Gaaffii Gonfoo%'))
        )
        
        warning_query = DisciplineRecord.query.join(Employee, DisciplineRecord.employee_id == Employee.id).filter(
            db.cast(Employee.branch_id, db.String) == b_id_str,
            DisciplineRecord.penalty_type.ilike('%akeekkachiisa%')
        )
        
        penalty_query = DisciplineRecord.query.join(Employee, DisciplineRecord.employee_id == Employee.id).filter(
            db.cast(Employee.branch_id, db.String) == b_id_str,
            db.not_(DisciplineRecord.penalty_type.ilike('%akeekkachiisa%'))
        )
        
        local_committee = DisciplineRecord.query.join(Employee).filter(db.cast(Employee.branch_id, db.String) == b_id_str, db.or_(DisciplineRecord.discipline_status == 'mana_sirreessaa', DisciplineRecord.discipline_status == None)).count()
        zone_committee = DisciplineRecord.query.join(Employee).filter(db.cast(Employee.branch_id, db.String) == b_id_str, DisciplineRecord.discipline_status == 'godinaa').count()
        commission_pending = DisciplineRecord.query.join(Employee).filter(db.cast(Employee.branch_id, db.String) == b_id_str, DisciplineRecord.discipline_status == 'komishinii').count()
        final_decided = DisciplineRecord.query.join(Employee).filter(db.cast(Employee.branch_id, db.String) == b_id_str, DisciplineRecord.discipline_status == 'murtaae').count()

    retired_count = len(get_retired_employees_list(all_active_for_retired))

    resigned_statuses = ['Resigned', 'Terminated', "Du'aan", 'Fedhiitiin', 'Dhukkubaan', 'Dismissed']
    if branch_id == 'all':
        resigned_count = Employee.query.filter(Employee.status.in_(resigned_statuses)).count()
    else:
        resigned_count = Employee.query.filter(
            db.cast(Employee.branch_id, db.String) == str(branch_id),
            Employee.status.in_(resigned_statuses)
        ).count()

    data = {
        "total": emp_query.count(),
        "active": emp_query.count(),
        "male": emp_query.filter(db.or_(Employee.gender == 'Dhiira', Employee.gender == 'Dhiirra')).count(),
        "female": emp_query.filter(db.or_(Employee.gender == 'Dhalaa', Employee.gender == 'Dubartii')).count(),
        "retired": retired_count,
        "resigned": resigned_count,
        "transfers": trans_query.count(),
        "promotions": promo_query.count(),
        "warning": warning_query.count(),
        "penalty": penalty_query.count(),
        "clean": emp_query.count(),
        "local_committee": local_committee,
        "zone_committee": zone_committee,
        "commission_pending": commission_pending,
        "final_decided": final_decided
    }
    return jsonify(data)

@app.route('/warnings')
@login_required
def warnings():
    branch_id_filter = request.args.get('branch_id')
    status_filter = request.args.get('status')
    
    query = DisciplineRecord.query.join(Employee, DisciplineRecord.employee_id == Employee.id)
    
    if status_filter:
        if status_filter == 'mana_sirreessaa':
            query = query.filter(db.or_(DisciplineRecord.discipline_status == 'mana_sirreessaa', DisciplineRecord.discipline_status == None))
        else:
            query = query.filter(DisciplineRecord.discipline_status == status_filter)

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
    return render_template('warnings.html', records=records, all_branches=all_branches, selected_branch=branch_id_filter, selected_status=status_filter)

@app.route('/delete_discipline/<int:id>', methods=['POST'])
@login_required
def delete_discipline(id):
    record = DisciplineRecord.query.get_or_404(id)
    user_b_val = int(current_user.branch_id) if current_user.branch_id and str(current_user.branch_id).isdigit() else current_user.branch_id
    if current_user.role != 'admin' and record.employee and record.employee.branch_id != user_b_val:
        abort(403)
        
    try:
        create_local_backup()
        db.session.delete(record)
        db.session.commit()
        flash("Galmeen naamusaa milkaa'inaan tarree irraa haqameera!", 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Dogoggorri uumameera: {str(e)}', 'danger')
        
    return redirect(request.referrer or url_for('warnings'))

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
                date_given=d_date,
                local_committee_date=request.form.get('local_committee_date'),
                zone_committee_date=request.form.get('zone_committee_date'),
                commission_sent_date=request.form.get('commission_sent_date'),
                discipline_status=request.form.get('discipline_status', 'mana_sirreessaa'),
                final_decision=request.form.get('final_decision')
            )
            db.session.add(new_record)
            db.session.commit()
            flash("Odeeffannoon naamusa hojjetaa milkaa'inaan galmaa'eera!", 'success')
            return redirect(url_for('warnings'))
        except Exception as e:
            db.session.rollback()
            flash(f'Dogoggorri uumameera: {str(e)}', 'danger')

    return render_template('add_discipline.html', employee=emp)

@app.route('/update_transfer_status/<int:id>', methods=['POST'])
@login_required
def update_transfer_status(id):
    transfer = Transfer.query.get_or_404(id)
    try:
        create_local_backup()
        status = request.form.get('status')
        if status:
            transfer.status = status
            db.session.commit()
            flash("Haalli jijjiirraa milkaa'inaan fooyya'eera!", 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Dogoggorri uumameera: {str(e)}', 'danger')
    return redirect(url_for('transfers'))

@app.route('/add_transfer', methods=['POST'])
@login_required
def add_transfer():
    try:
        create_local_backup()
        employee_id = request.form.get('employee_id')
        from_branch_id = request.form.get('from_branch_id')
        to_branch_id = request.form.get('to_branch_id')
        reason = request.form.get('reason')
        transfer_date = request.form.get('transfer_date') or request.form.get('date')

        new_transfer = Transfer(
            employee_id=int(employee_id) if employee_id and str(employee_id).isdigit() else None,
            from_branch_id=int(from_branch_id) if from_branch_id and str(from_branch_id).isdigit() else None,
            to_branch_id=int(to_branch_id) if to_branch_id and str(to_branch_id).isdigit() else None,
            reason=reason,
            date_given=transfer_date,
            status='Pending'
        )
        db.session.add(new_transfer)
        
        if employee_id and to_branch_id and str(employee_id).isdigit() and str(to_branch_id).isdigit():
            emp = Employee.query.get(int(employee_id))
            if emp:
                emp.branch_id = int(to_branch_id)

        db.session.commit()
        flash("Jijjiirraan hojjetaa milkaa'inaan galmaa'eera!", 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Dogoggorri uumameera: {str(e)}', 'danger')

    return redirect(url_for('transfers'))

@app.route('/add_rank', methods=['POST'])
@login_required
def add_rank():
    try:
        create_local_backup()
        name = request.form.get('name')
        description = request.form.get('description', '')
        if name:
            new_rank = Rank(name=name, description=description)
            db.session.add(new_rank)
            db.session.commit()
            flash("Gulantaan haaraan milkaa'inaan galmaa'eera!", 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Dogoggorri uumameera: {str(e)}', 'danger')
    return redirect(url_for('ranks'))

@app.route('/update_rank_status/<int:id>', methods=['POST'])
@login_required
def update_rank_status(id):
    rank = Rank.query.get_or_404(id)
    try:
        create_local_backup()
        name = request.form.get('name')
        description = request.form.get('description')
        if name:
            rank.name = name
        if description is not None:
            rank.description = description
        db.session.commit()
        flash("Gulantaan milkaa'inaan fooyya'eera!", 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Dogoggorri uumameera: {str(e)}', 'danger')
    return redirect(url_for('ranks'))

@app.route('/delete_rank/<int:id>', methods=['POST'])
@login_required
def delete_rank(id):
    rank = Rank.query.get_or_404(id)
    try:
        create_local_backup()
        db.session.delete(rank)
        db.session.commit()
        flash("Gulantaan milkaa'inaan haqameera!", 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Dogoggorri uumameera: {str(e)}', 'danger')
    return redirect(url_for('ranks'))

@app.route('/add_employee', methods=['POST'])
@login_required
def add_employee():
    try:
        create_local_backup()
        full_name = request.form.get('full_name')
        unique_id = request.form.get('unique_id')
        pension_number = request.form.get('pension_number')
        phone_number = request.form.get('phone_number')
        gender = request.form.get('gender')
        
        if current_user.role == 'admin':
            branch_id = request.form.get('branch_id')
        else:
            branch_id = current_user.branch_id

        rank_id = request.form.get('rank_id')
        job_position = request.form.get('job_position')
        education_level = request.form.get('education_level')
        field_of_study = request.form.get('field_of_study')
        rank_salary = float(request.form.get('rank_salary', 0) or 0)
        location_allowance = float(request.form.get('location_allowance', 0) or 0)
        food_allowance = float(request.form.get('food_allowance', 0) or 0)
        hire_date = request.form.get('hire_date')
        birth_date = request.form.get('birth_date')
        rank_date = request.form.get('rank_date')

        new_emp = Employee(
            full_name=full_name,
            unique_id=unique_id,
            pension_number=pension_number,
            phone_number=phone_number,
            gender=gender,
            branch_id=int(branch_id) if branch_id and str(branch_id).isdigit() else None,
            rank_id=int(rank_id) if rank_id and str(rank_id).isdigit() else None,
            job_position=job_position,
            education_level=education_level,
            field_of_study=field_of_study,
            rank_salary=rank_salary,
            location_allowance=location_allowance,
            food_allowance=food_allowance,
            hire_date=hire_date,
            birth_date=birth_date,
            rank_date=rank_date,
            status='Active'
        )
        db.session.add(new_emp)
        db.session.commit()
        flash("Hojjetaan haaraan milkaa'inaan galmaa'eera!", 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Dogoggorri uumameera: {str(e)}', 'danger')

    return redirect(url_for('employees'))

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
            emp.perf_score = float(request.form.get('perf_score', 0) or 0)
            emp.edu_score = float(request.form.get('edu_score', 0) or 0)
            emp.discipline_score = float(request.form.get('discipline_score', 0) or 0)
            emp.law_score = float(request.form.get('law_score', 0) or 0)
            emp.experience_score = float(request.form.get('experience_score', 0) or 0)
            emp.service_score = float(request.form.get('service_score', 0) or 0)
            
            emp.total_score = (emp.perf_score + emp.edu_score + emp.discipline_score + 
                               emp.law_score + emp.experience_score + emp.service_score)
            
            db.session.commit()
            flash("Qabxiin madaallii hojjetaa milkaa'inaan galmaa'eera!", 'success')
            return redirect(url_for('employees'))
        except Exception as e:
            db.session.rollback()
            flash(f'Dogoggorri uumameera: {str(e)}', 'danger')

    return render_template('evaluate_employee.html', employee=emp)

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
            emp.full_name = request.form.get('full_name', emp.full_name)
            emp.unique_id = request.form.get('unique_id', emp.unique_id)
            emp.pension_number = request.form.get('pension_number', emp.pension_number)
            emp.phone_number = request.form.get('phone_number', emp.phone_number)
            emp.gender = request.form.get('gender', emp.gender)
            if current_user.role == 'admin':
                b_id = request.form.get('branch_id')
                if b_id:
                    emp.branch_id = int(b_id)
            
            rank_id = request.form.get('rank_id')
            if rank_id and str(rank_id).isdigit():
                emp.rank_id = int(rank_id)
                
            emp.job_position = request.form.get('job_position', emp.job_position)
            emp.education_level = request.form.get('education_level', emp.education_level)
            emp.field_of_study = request.form.get('field_of_study', emp.field_of_study)
            emp.rank_salary = float(request.form.get('rank_salary', 0) or 0)
            emp.location_allowance = float(request.form.get('location_allowance', 0) or 0)
            emp.food_allowance = float(request.form.get('food_allowance', 0) or 0)
            emp.hire_date = request.form.get('hire_date', emp.hire_date)
            emp.birth_date = request.form.get('birth_date', emp.birth_date)
            emp.rank_date = request.form.get('rank_date', emp.rank_date)
            emp.status = request.form.get('status', emp.status)

            db.session.commit()
            flash("Odeeffannoon hojjetaa milkaa'inaan fooyya'eera!", 'success')
            return redirect(url_for('employees'))
        except Exception as e:
            db.session.rollback()
            flash(f'Dogoggorri uumameera: {str(e)}', 'danger')

    all_branches = Branch.query.all()
    all_ranks = Rank.query.all()
    return render_template('edit_employee.html', employee=emp, branches=all_branches, ranks=all_ranks)

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
        flash("Hojjetaan milkaa'inaan haqameera!", 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Dogoggorri uumameera: {str(e)}', 'danger')
        
    return redirect(url_for('employees'))

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

@app.route('/employees')
@login_required
def employees():
    branch_id = request.args.get('branch_id')
    rank = request.args.get('rank')
    gender = request.args.get('gender')
    search_query = request.args.get('search', '')
    status_filter = request.args.get('status', 'Active')
    
    rank_status = request.args.get('rank_status')          
    position_status = request.args.get('position_status')  
    allowance_status = request.args.get('allowance_status')

    query = Employee.query
    if status_filter != 'All':
        query = query.filter_by(status=status_filter)

    if current_user.role != 'admin':
        branch_id = current_user.branch_id
        query = query.filter_by(branch_id=int(branch_id) if branch_id and str(branch_id).isdigit() else branch_id)
    elif branch_id:
        query = query.filter_by(branch_id=int(branch_id) if branch_id.isdigit() else branch_id)

    if rank_status == 'with':
        query = query.filter(Employee.rank_id != None)
    elif rank_status == 'without':
        query = query.filter(Employee.rank_id == None)

    if position_status == 'with':
        query = query.filter(Employee.job_position != None, Employee.job_position != '')
    elif position_status == 'without':
        query = query.filter(db.or_(Employee.job_position == None, Employee.job_position == ''))

    if allowance_status == 'with':
        query = query.filter(Employee.location_allowance > 0)
    elif allowance_status == 'without':
        query = query.filter(db.or_(Employee.location_allowance == None, Employee.location_allowance == 0))

    if search_query:
        query = query.filter(
            db.or_(
                Employee.full_name.ilike(f'%{search_query}%'),
                Employee.unique_id.ilike(f'%{search_query}%'),
                Employee.job_position.ilike(f'%{search_query}%')
            )
        )

    all_employees = query.order_by(Employee.full_name.asc()).all()
    all_branches = Branch.query.all() if current_user.role == 'admin' else Branch.query.filter_by(id=current_user.branch_id).all()
    all_ranks = Rank.query.all()
    return render_template('employees.html', employees=all_employees, branches=all_branches, ranks=all_ranks)

@app.route('/ranks')
@login_required
def ranks():
    all_ranks = Rank.query.all()
    return render_template('ranks.html', ranks=all_ranks)

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
                db.or_(Employee.branch_id == b_id_int, Transfer.to_branch_id == b_id_int)
            )
        promotions_list = query.all()
    else:
        user_b = current_user.branch_id
        promotions_list = query.join(Employee, Transfer.employee_id == Employee.id).filter(Employee.branch_id == user_b).all() if user_b else []

    return render_template('promotions.html', promotions=promotions_list, all_branches=all_branches, selected_branch=branch_id_filter, selected_status=status_filter)

@app.route('/penalties')
@login_required
def penalties():
    branch_id_filter = request.args.get('branch_id')
    query = DisciplineRecord.query.join(Employee, DisciplineRecord.employee_id == Employee.id)
    if current_user.role == 'admin':
        if branch_id_filter and str(branch_id_filter).isdigit():
            query = query.filter(Employee.branch_id == int(branch_id_filter))
    else:
        user_b = current_user.branch_id
        query = query.filter(Employee.branch_id == user_b) if user_b else query.filter(False)
    records = query.all()
    all_branches = Branch.query.all()
    return render_template('penalties.html', records=records, all_branches=all_branches, selected_branch=branch_id_filter)

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
        df.to_excel(output, index=False, sheet_name='Miseensota')
    output.seek(0)
    return send_file(
        output, 
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', 
        as_attachment=True, 
        download_name='HRKMSO_Report.xlsx'
    )

@app.route('/export_promotions_excel')
@login_required
def export_promotions_excel():
    branch_id = request.args.get('branch_id')
    status_filter = request.args.get('status', 'Pending')

    query = Transfer.query.filter(Transfer.reason.ilike('%Gaaffii Gonfoo%'))

    if status_filter and status_filter != 'All':
        query = query.filter_by(status=status_filter)

    if current_user.role == 'admin':
        if branch_id and str(branch_id).isdigit():
            b_id_int = int(branch_id)
            query = query.join(Employee, Transfer.employee_id == Employee.id).filter(
                db.or_(Employee.branch_id == b_id_int, Transfer.to_branch_id == b_id_int)
            )
        promotions_list = query.all()
    else:
        user_b = current_user.branch_id
        promotions_list = query.join(Employee, Transfer.employee_id == Employee.id).filter(Employee.branch_id == user_b).all() if user_b else []

    if not promotions_list:
        flash("Odeeffannoon gaaffii gonfoo Excel-tti buufamu hin jiru!", 'warning')
        return redirect(url_for('promotions'))

    data = []
    for idx, p in enumerate(promotions_list, start=1):
        emp_name = p.employee.full_name if p.employee else 'N/A'
        data.append({
            'Lakk.': idx,
            'Maqaa Hojjetaa': emp_name,
            'Gonfoo Duraanii': getattr(p, 'from_rank', '-'),
            'Gonfoo Haaraa': getattr(p, 'to_rank', '-'),
            'Sababa': p.reason if p.reason else '-',
            'Status': getattr(p, 'status', '-')
        })

    df = pd.DataFrame(data)
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Gaaffii Gonfoo')
    output.seek(0)

    return send_file(
        output, 
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', 
        as_attachment=True, 
        download_name='Gaaffii_Gonfoo_Report.xlsx'
    )

@app.route('/export_ranks_excel')
@login_required
def export_ranks_excel():
    all_ranks = Rank.query.all()
    if not all_ranks:
        flash("Odeeffannoon gulantaa Excel-tti buufamu hin jiru!", 'warning')
        return redirect(url_for('ranks'))

    data = []
    for idx, r in enumerate(all_ranks, start=1):
        data.append({
            'Lakk.': idx,
            'Maqaa Gulantaa': r.name,
            'Ibsa': getattr(r, 'description', '-')
        })

    df = pd.DataFrame(data)
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(output, index=False, sheet_name='Gulantaalee')
    output.seek(0)
    return send_file(
        output, 
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', 
        as_attachment=True, 
        download_name='Ranks_Report.xlsx'
    )

@app.route('/retired_employees')
@login_required
def retired_employees():
    if current_user.role == 'admin':
        all_emps = Employee.query.filter_by(status='Active').all()
    else:
        user_b = current_user.branch_id
        b_val = int(user_b) if user_b and str(user_b).isdigit() else user_b
        all_emps = Employee.query.filter_by(branch_id=b_val, status='Active').all() if user_b else []
    
    retired_list = get_retired_employees_list(all_emps)
    return render_template('retired_employees.html', retired_list=retired_list)

@app.route('/resigned_employees')
@login_required
def resigned_employees():
    inactive_statuses = ['Resigned', 'Terminated', "Du'aan", 'Fedhiitiin', 'Dhukkubaan', 'Dismissed']
    if current_user.role == 'admin':
        resigned_list = Employee.query.filter(Employee.status.in_(inactive_statuses)).all()
    else:
        user_b = current_user.branch_id
        b_val = int(user_b) if user_b and str(user_b).isdigit() else user_b
        resigned_list = Employee.query.filter_by(branch_id=b_val).filter(Employee.status.in_(inactive_statuses)).all() if user_b else []
        
    return render_template('resigned_employees.html', resigned_list=resigned_list)

@app.route('/users')
@login_required
@admin_required
def users():
    all_users = User.query.all()
    all_branches = Branch.query.all()
    return render_template('users.html', users=all_users, all_branches=all_branches)

@app.route('/add_user', methods=['POST'])
@login_required
@admin_required
def add_user():
    try:
        create_local_backup()
        username = request.form.get('username')
        password = request.form.get('password')
        role = request.form.get('role', 'branch_user')
        branch_id = request.form.get('branch_id')
        
        if User.query.filter_by(username=username).first():
            flash('Maqaan fayyadamaa kun duraan jira!', 'danger')
            return redirect(url_for('users'))
            
        hashed_pw = generate_password_hash(password)
        new_user = User(
            username=username,
            password=hashed_pw,
            role=role,
            branch_id=int(branch_id) if branch_id and str(branch_id).isdigit() else None
        )
        db.session.add(new_user)
        db.session.commit()
        flash("Fayyadamaan haaraan milkaa'inaan uumameera!", 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Dogoggorri uumameera: {str(e)}', 'danger')
    return redirect(url_for('users'))

@app.route('/edit_user/<int:id>', methods=['POST'])
@login_required
@admin_required
def edit_user(id):
    user = User.query.get_or_404(id)
    try:
        create_local_backup()
        user.username = request.form.get('username', user.username)
        user.role = request.form.get('role', user.role)
        branch_id = request.form.get('branch_id')
        user.branch_id = int(branch_id) if branch_id and str(branch_id).isdigit() else None
        
        new_password = request.form.get('password')
        if new_password and new_password.strip():
            user.password = generate_password_hash(new_password.strip())
            
        db.session.commit()
        flash("Odeeffannoon fayyadamaa milkaa'inaan fooyya'eera!", 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Dogoggorri uumameera: {str(e)}', 'danger')
    return redirect(url_for('users'))

@app.route('/delete_user/<int:id>', methods=['POST'])
@login_required
@admin_required
def delete_user(id):
    if id == current_user.id:
        flash("Fayyadamaa amma itti fayyadamtu haquun hin danda'amu!", 'danger')
        return redirect(url_for('users'))
    user = User.query.get_or_404(id)
    try:
        create_local_backup()
        db.session.delete(user)
        db.session.commit()
        flash("Fayyadamaan milkaa'inaan haqameera!", 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Dogoggorri uumameera: {str(e)}', 'danger')
    return redirect(url_for('users'))

@app.route('/generate-letter', methods=['POST'])
@login_required
def generate_letter():
    letter_type = request.form.get('letter_type')
    raw_gg = request.form.get('gg_list', '')
    gg_entries = [line.strip() for line in raw_gg.splitlines() if line.strip()] if raw_gg else request.form.getlist('gg_list')

    job_position_val = ''
    for val in request.form.getlist('job_position'):
        if val and val.strip():
            job_position_val = val.strip()
            break
    if not job_position_val:
        job_position_val = request.form.get('job_position', '')

    letter_data = {
        'letter_type': letter_type,
        'emp_rank_name': request.form.get('emp_rank_name', ''),
        'directive_no': request.form.get('directive_no', ''),
        'effective_date': request.form.get('effective_date', ''),
        'from_rank': request.form.get('from_rank', ''),
        'to_rank': request.form.get('to_rank', ''),
        'rank_salary': float(request.form.get('rank_salary', 0) or 0),
        'previous_salary': float(request.form.get('previous_salary', 0) or 0),
        'salary_diff': float(request.form.get('salary_diff', 0) or 0),
        'food_allowance': float(request.form.get('food_allowance', 0) or 0),
        'requesting_body': request.form.get('requesting_body', ''),
        'meeting_date': request.form.get('meeting_date', ''),
        'branch_name': request.form.get('branch_name', ''),
        'from_branch': request.form.get('from_branch', ''),
        'to_branch': request.form.get('to_branch', ''),
        'from_branch_short': request.form.get('from_branch_short', ''),
        'to_branch_short': request.form.get('to_branch_short', ''),
        'reason': request.form.get('reason', ''),
        'job_position': job_position_val,
        'salary': float(request.form.get('salary', 0) or 0),
        'budget_name': request.form.get('budget_name', ''),
        'gg_list': gg_entries
    }
    return render_template('official_letters_print_2.html', letter=letter_data)

if __name__ == '__main__':
    app.run(debug=True)