import os
import io
import shutil
from datetime import datetime, date
from flask import Flask, render_template, redirect, url_for, request, flash, abort, send_file, jsonify
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from models import db, User, Employee, Branch, Rank, Transfer, DisciplineRecord, AuditLog, EmployeeDocument
from sqlalchemy.exc import IntegrityError
from functools import wraps
import pandas as pd

# --- PROFESSIONAL ICT & SECURITY EXTENSIONS ---
import sentry_sdk
from sentry_sdk.integrations.flask import FlaskIntegration
from flask_migrate import Migrate
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_mail import Mail, Message

# Sentry Error Monitoring Qindeessuu
sentry_sdk.init(
    dsn=os.environ.get("SENTRY_DSN", "YOUR_SENTRY_DSN_HERE"),
    integrations=[FlaskIntegration()],
    traces_sample_rate=1.0,
    environment="production"
)

# Supabase Client import gochuu fi qindeessuu
try:
    from supabase import create_client, Client
    SUPABASE_URL = os.environ.get("SUPABASE_URL", "").strip()
    SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "").strip()
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY) if SUPABASE_URL and SUPABASE_KEY else None
except Exception:
    supabase = None

try:
    from py_ethiopian_date_converter import to_ethiopian, to_gregorian
except ImportError:
    def to_ethiopian(year, month, day):
        return year - 8, month, day
    def to_gregorian(year, month, day):
        return year + 8, month, day

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'hrkmso-secret-key-2026')

# Flask-Migrate fi Flask-Limiter Qindeessuu
migrate = Migrate(app, db)
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)

# Flask-Mail Qindeessuu (Backup Notificationaf) - Sirreeffameera
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USE_SSL'] = False
app.config['MAIL_USERNAME'] = 'amanuel8238@gmail.com'
app.config['MAIL_PASSWORD'] = 'vlflxhncwsyzvkdo'
app.config['MAIL_DEFAULT_SENDER'] = 'amanuel8238@gmail.com'
mail = Mail(app)

# Folder Document attachments itti kufu
DOCUMENTS_FOLDER = os.path.join(app.root_path, 'static', 'uploads', 'documents')
if not os.path.exists(DOCUMENTS_FOLDER):
    os.makedirs(DOCUMENTS_FOLDER)
app.config['DOCUMENTS_FOLDER'] = DOCUMENTS_FOLDER
ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg', 'docx'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def format_ethiopian_date(date_str):
    if not date_str or str(date_str).strip() in ['', 'None', 'Hin ibsamne']:
        return "Hin ibsamne"
    try:
        s = str(date_str).strip()
        if s.isdigit() and len(s) == 4:
            g_year = int(s)
            return str(g_year - 8)
        
        if '-' in s:
            parts = s.split()[0].split('-')
            if len(parts) == 3:
                gy, gm, gd = int(parts[0]), int(parts[1]), int(parts[2])
                ey, em, ed = to_ethiopian(gy, gm, gd)
                return f"{ed:02d}/{em:02d}/{ey}"
        elif '/' in s:
            parts = s.split()[0].split('/')
            if len(parts) == 3:
                if len(parts[2]) == 4:
                    gd, gm, gy = int(parts[0]), int(parts[1]), int(parts[2])
                    ey, em, ed = to_ethiopian(gy, gm, gd)
                    return f"{ed:02d}/{em:02d}/{ey}"
        return s
    except Exception:
        return str(date_str)

Employee.previous_rank_date = property(lambda self: format_ethiopian_date(getattr(self, 'rank_date', None) or getattr(self, 'last_promotion_date', None)))
Employee.eth_next_promotion_date = property(lambda self: format_ethiopian_date(getattr(self, 'next_promotion_date', None)))

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

def calculate_service_duration(hire_date):
    if not hire_date:
        return "Hin beekamu"
    try:
        h_str = str(hire_date).strip().split()[0]
        h_year, h_month = None, 1
        
        if '-' in h_str:
            parts = h_str.split('-')
            if len(parts[0]) == 4:
                h_year, h_month = int(parts[0]), int(parts[1])
            else:
                h_year, h_month = int(parts[2]), int(parts[1])
        elif '/' in h_str:
            parts = h_str.split('/')
            if len(parts) == 3:
                h_year = int(parts[2]) if len(parts[2]) == 4 else int(parts[0])
                h_month = int(parts[0]) if len(parts[2]) == 4 else int(parts[1])
        elif h_str.isdigit() and len(h_str) == 4:
            h_year = int(h_str)

        if h_year:
            current_eth_year = 2019
            current_eth_month = 2
            
            years = current_eth_year - h_year
            months = current_eth_month - h_month
            
            if months < 0:
                years -= 1
                months += 12
                
            if years < 0:
                return "Haaraa"
                
            result = []
            if years > 0:
                result.append(f"Waggaa {years}")
            if months > 0 or not result:
                result.append(f"Ji'a {months}")
            return " fi ".join(result)
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
    return dict(
        endpoint_exists=endpoint_exists, 
        calculate_age=calculate_age, 
        format_ethiopian_date=format_ethiopian_date,
        calculate_service_duration=calculate_service_duration
    )

instance_dir = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'instance')
if not os.path.exists(instance_dir):
    os.makedirs(instance_dir)

app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get(
    'DATABASE_URL', 
    'postgresql://postgres.jspbjzjutnwidvsoayna:Ame_2018%23Strong!9X@aws-0-eu-west-1.pooler.supabase.com:5432/postgres'
)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# 👇 ENGINE POOL OPTIONS (CONNECTION DROPS FI TIMEOUT FURUUF) 👇
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    "pool_pre_ping": True,
    "pool_recycle": 300,
    "pool_timeout": 30,
}

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

# Automated Backup Email Notification Function
def send_backup_notification(filename):
    try:
        admin_email = os.environ.get('ADMIN_EMAIL', 'amanuel8238@gmail.com')
        msg = Message("HRKMSO Backup Milkaa'eera",
                      sender=app.config['MAIL_USERNAME'],
                      recipients=[admin_email])
        msg.body = f"Galmeen backup {filename} milkaa'inaan uumamee Supabase storage fi local irratti kuufameera."
        mail.send(msg)
    except Exception as e:
        print(f"[ERR] Email erguu irratti dogoggorri uumame: {e}")

# Local & Supabase Backup System
def create_local_backup():
    try:
        db_path = os.path.join(instance_dir, 'hrkmso.db')
        backup_dir = 'backups'
        if not os.path.exists(backup_dir):
            os.makedirs(backup_dir)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_filename = f'hrkmso_backup_{timestamp}.db'
        backup_file_path = os.path.join(backup_dir, backup_filename)
        
        if os.path.exists(db_path):
            shutil.copy(db_path, backup_file_path)
            print(f"[INFO] Local Backup successful: {backup_file_path}")
            
            if supabase:
                try:
                    with open(backup_file_path, 'rb') as f:
                        res = supabase.storage.from_('hrkmso-backups').upload(
                            path=backup_filename,
                            file=f,
                            file_options={"content-type": "application/x-sqlite3"}
                        )
                    print(f"[INFO] Supabase Storage upload successful: {backup_filename}")
                except Exception as ex:
                    print(f"[ERR] Supabase Storage upload error: {ex}")
            else:
                print("[WARN] Supabase client is not initialized (Check URL/KEY).")
            
            send_backup_notification(backup_filename)
    except Exception as e:
        print(f"[ERR] Backup error: {e}")

@app.route('/admin/trigger-backup', methods=['POST', 'GET'])
@login_required
@admin_required
def trigger_backup():
    try:
        create_local_backup()
        db_path = os.path.join(instance_dir, 'hrkmso.db')
        
        if os.path.exists(db_path):
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            return send_file(
                db_path,
                as_attachment=True,
                download_name=f'hrkmso_backup_{timestamp}.db'
            )
        
        flash("Database backup milkaa'inaan uumameera!", "success")
    except Exception as e:
        flash(f"Backup uumuu irratti dogoggorri uumameera: {e}", "danger")
        
    return redirect(url_for('dashboard'))

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
                conn.execute(sa.text("ALTER TABLE discipline_record ADD COLUMN discipline_status VARCHAR(100) DEFAULT 'pending'"))
            if 'final_decision' not in disc_columns:
                conn.execute(sa.text("ALTER TABLE discipline_record ADD COLUMN final_decision TEXT"))
            if 'offense_type' not in disc_columns:
                conn.execute(sa.text("ALTER TABLE discipline_record ADD COLUMN offense_type VARCHAR(150)"))
            if 'expiry_date' not in disc_columns:
                conn.execute(sa.text("ALTER TABLE discipline_record ADD COLUMN expiry_date VARCHAR(50)"))
            if 'approved_by' not in disc_columns:
                conn.execute(sa.text("ALTER TABLE discipline_record ADD COLUMN approved_by VARCHAR(150)"))

    if 'transfer' in inspector.get_table_names():
        transfer_columns = [col['name'] for col in inspector.get_columns('transfer')]
        with engine.begin() as conn:
            if 'approval_reason' not in transfer_columns:
                conn.execute(sa.text("ALTER TABLE transfer ADD COLUMN approval_reason TEXT"))
            if 'from_branch_id' not in transfer_columns:
                conn.execute(sa.text("ALTER TABLE transfer ADD COLUMN from_branch_id INTEGER"))
            if 'to_branch_id' not in transfer_columns:
                conn.execute(sa.text("ALTER TABLE transfer ADD COLUMN to_branch_id INTEGER"))

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

# Route Document Attachments Upload Gochuuf
@app.route('/upload_document/<int:employee_id>', methods=['POST'])
@login_required
def upload_document(employee_id):
    emp = Employee.query.get_or_404(employee_id)
    user_b_val = int(current_user.branch_id) if current_user.branch_id and str(current_user.branch_id).isdigit() else current_user.branch_id
    if current_user.role != 'admin' and emp.branch_id != user_b_val:
        abort(403)

    try:
        create_local_backup()
        doc_name = request.form.get('document_name') or 'Ragaa Miseensaa'
        files = request.files.getlist('documents')
        
        if not files or files[0].filename == '':
            flash('Faayiliin tokkollee hin filatamne!', 'danger')
            return redirect(request.referrer or url_for('employees'))

        uploaded_count = 0
        for file in files:
            if file and allowed_file(file.filename):
                sec_filename = secure_filename(file.filename)
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f"emp_{emp.id}_{timestamp}_{sec_filename}"
                file_path = os.path.join(app.config['DOCUMENTS_FOLDER'], filename)
                
                file.save(file_path)
                
                if supabase:
                    try:
                        with open(file_path, 'rb') as f_stream:
                            supabase.storage.from_('hrkmso-documents').upload(
                                path=filename,
                                file=f_stream,
                                file_options={"content-type": file.content_type or "application/pdf"}
                            )
                    except Exception as s_err:
                        print(f"[WARN] Supabase Document upload error: {s_err}")
                        
                doc_record = EmployeeDocument(
                    employee_id=emp.id,
                    document_name=doc_name,
                    file_url=filename
                )
                db.session.add(doc_record)
                uploaded_count += 1

        if uploaded_count > 0:
            log_entry = AuditLog(
                user_id=current_user.id,
                action="Ragaa Attach Godhe",
                details=f"Hojjetaaf {emp.full_name} ragaaleen {uploaded_count} attach ta'aniiru."
            )
            db.session.add(log_entry)
            db.session.commit()
            flash(f"Ragaaleen {uploaded_count} milkaa'inaan galmeesaaf attach ta'aniiru!", 'success')
        else:
            flash("Gosti faayilii filatame hin eyyamamu (PDF, JPG, PNG, DOCX qofa)!", 'danger')
    except Exception as e:
        db.session.rollback()
        flash(f'Dogoggorri uumameera: {str(e)}', 'danger')

    return redirect(request.referrer or url_for('employees'))

# Static uploads route to handle local missing files via Supabase
@app.route('/static/uploads/documents/<filename>')
def uploaded_document(filename):
    file_path = os.path.join(app.config['DOCUMENTS_FOLDER'], filename)
    if os.path.exists(file_path):
        return send_file(file_path)
    
    # Yoo local irratti hin jirre (Render ephemeral storage irraa kan ka'e haqame), Supabase irraa barbaadi
    if supabase:
        try:
            res = supabase.storage.from_('hrkmso-documents').get_public_url(filename)
            if res:
                return redirect(res)
        except Exception as e:
            print(f"[ERR] Supabase file fetch error: {e}")
            
    abort(404)

# 👇 FOOYYA'EERA: create_local_backup() ASII HAQAMEERA (TIMEOUT AKKA HIN FIDNEEF) 👇
@app.route('/delete_document/<int:id>', methods=['POST'])
@login_required
def delete_document(id):
    doc = EmployeeDocument.query.get_or_404(id)
    emp = doc.employee
    user_b_val = int(current_user.branch_id) if current_user.branch_id and str(current_user.branch_id).isdigit() else current_user.branch_id
    if current_user.role != 'admin' and emp and emp.branch_id != user_b_val:
        abort(403)

    try:
        file_path = os.path.join(app.config['DOCUMENTS_FOLDER'], doc.file_url)
        if os.path.exists(file_path):
            os.remove(file_path)
            
        db.session.delete(doc)
        db.session.commit()
        flash("Ragaan attach ta'ee ture milkaa'inaan haqameera!", 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Dogoggorri uumameera: {str(e)}', 'danger')

    return redirect(request.referrer or url_for('employees'))

@app.route('/login', methods=['GET', 'POST'])
@limiter.limit("5 per minute")
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
            
            log_entry = AuditLog(
                user_id=user.id,
                action="Seensa (Login)",
                details=f"Fayyadamaan {user.username} systemitti seeneera."
            )
            db.session.add(log_entry)
            db.session.commit()

            next_page = request.args.get('next')
            return redirect(next_page or url_for('dashboard'))
        else:
            flash('Maqaa fayyadamaa ykn jecha iccitii dogoggortee jirta.', 'danger')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    log_entry = AuditLog(
        user_id=current_user.id,
        action="Ba'umsa (Logout)",
        details=f"Fayyadamaan {current_user.username} system irraa ba'eera."
    )
    db.session.add(log_entry)
    db.session.commit()

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
        
        local_committee_count = DisciplineRecord.query.filter(
            DisciplineRecord.local_committee_date != None,
            DisciplineRecord.local_committee_date != ''
        ).count()
        
        zone_committee_count = DisciplineRecord.query.filter(
            DisciplineRecord.zone_committee_date != None,
            DisciplineRecord.zone_committee_date != ''
        ).count()
        
        commission_pending_count = DisciplineRecord.query.filter(
            DisciplineRecord.commission_sent_date != None,
            DisciplineRecord.commission_sent_date != ''
        ).count()
        
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
            
            local_committee_count = DisciplineRecord.query.join(Employee).filter(
                Employee.branch_id == branch_id_val,
                DisciplineRecord.local_committee_date != None,
                DisciplineRecord.local_committee_date != ''
            ).count()

            zone_committee_count = DisciplineRecord.query.join(Employee).filter(
                Employee.branch_id == branch_id_val,
                DisciplineRecord.zone_committee_date != None,
                DisciplineRecord.zone_committee_date != ''
            ).count()

            commission_pending_count = DisciplineRecord.query.join(Employee).filter(
                Employee.branch_id == branch_id_val,
                DisciplineRecord.commission_sent_date != None,
                DisciplineRecord.commission_sent_date != ''
            ).count()

            final_decided_count = DisciplineRecord.query.join(Employee).filter(
                Employee.branch_id == branch_id_val,
                DisciplineRecord.discipline_status == 'murtaae'
            ).count()
        else:
            transfer_count = 0
            local_committee_count = zone_committee_count = commission_pending_count = final_decided_count = 0

    retired_count = len(get_retired_employees_list(all_emps))
    
    if current_user.role == 'admin':
        warning_count = DisciplineRecord.query.filter(DisciplineRecord.penalty_type.ilike('%akeekkachiisa%')).count()
        penalty_count = DisciplineRecord.query.filter(db.not_(DisciplineRecord.penalty_type.ilike('%akeekkachiisa%'))).count()
        promotion_count = Transfer.query.filter(Transfer.reason.ilike('%Gaaffii Gonfoo%')).count()
    else:
        warning_count = DisciplineRecord.query.join(Employee, DisciplineRecord.employee_id == Employee.id).filter(
            Employee.branch_id == branch_id_val,
            DisciplineRecord.penalty_type.ilike('%akeekkachiisa%')
        ).count() if user_b else 0
        
        penalty_count = DisciplineRecord.query.join(Employee, DisciplineRecord.employee_id == Employee.id).filter(
            Employee.branch_id == branch_id_val,
            db.not_(DisciplineRecord.penalty_type.ilike('%akeekkachiisa%'))
        ).count() if user_b else 0

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
    if current_user.role != 'admin':
        branch_id = str(current_user.branch_id) if current_user.branch_id else '0'

    if branch_id == 'all':
        emp_query = Employee.query.filter_by(status='Active')
        all_active_for_retired = emp_query.all()
        promo_query = Transfer.query.filter(Transfer.reason.ilike('%Gaaffii Gonfoo%'))
        trans_query = Transfer.query.filter(db.not_(Transfer.reason.ilike('%Gaaffii Gonfoo%')))
        warning_query = DisciplineRecord.query.filter(DisciplineRecord.penalty_type.ilike('%akeekkachiisa%'))
        penalty_query = DisciplineRecord.query.filter(db.not_(DisciplineRecord.penalty_type.ilike('%akeekkachiisa%')))
        
        local_committee = DisciplineRecord.query.filter(
            DisciplineRecord.local_committee_date != None, DisciplineRecord.local_committee_date != ''
        ).count()
        zone_committee = DisciplineRecord.query.filter(
            DisciplineRecord.zone_committee_date != None, DisciplineRecord.zone_committee_date != ''
        ).count()
        commission_pending = DisciplineRecord.query.filter(
            DisciplineRecord.commission_sent_date != None, DisciplineRecord.commission_sent_date != ''
        ).count()
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
        
        local_committee = DisciplineRecord.query.join(Employee).filter(
            db.cast(Employee.branch_id, db.String) == b_id_str,
            DisciplineRecord.local_committee_date != None, DisciplineRecord.local_committee_date != ''
        ).count()
        
        zone_committee = DisciplineRecord.query.join(Employee).filter(
            db.cast(Employee.branch_id, db.String) == b_id_str,
            DisciplineRecord.zone_committee_date != None, DisciplineRecord.zone_committee_date != ''
        ).count()
        
        commission_pending = DisciplineRecord.query.join(Employee).filter(
            db.cast(Employee.branch_id, db.String) == b_id_str,
            DisciplineRecord.commission_sent_date != None, DisciplineRecord.commission_sent_date != ''
        ).count()
        
        final_decided = DisciplineRecord.query.join(Employee).filter(
            db.cast(Employee.branch_id, db.String) == b_id_str,
            DisciplineRecord.discipline_status == 'murtaae'
        ).count()

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
        if status_filter == 'pending':
            query = query.filter(db.or_(DisciplineRecord.discipline_status == 'pending', DisciplineRecord.discipline_status == None))
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
        if user_b:
            b_val = int(user_b) if str(user_b).isdigit() else user_b
            query = query.filter(Employee.branch_id == b_val)
        else:
            query = query.filter(False)
            
    records = query.all()
    all_branches = Branch.query.all()
    return render_template('penalties.html', records=records, all_branches=all_branches, selected_branch=branch_id_filter)

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

@app.route('/update_discipline_decision/<int:id>', methods=['POST'])
@login_required
@admin_required
def update_discipline_decision(id):
    record = DisciplineRecord.query.get_or_404(id)
    try:
        create_local_backup()
        final_decision = request.form.get('final_decision')
        discipline_status = request.form.get('discipline_status')
        
        if final_decision is not None:
            record.final_decision = final_decision.strip()
        if discipline_status is not None:
            record.discipline_status = discipline_status.strip()
            
        db.session.commit()
        flash("Murteen dhumaa fi status milkaa'inaan haaromfameera!", 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Dogoggorri uumameera: {str(e)}', 'danger')
    return redirect(url_for('warnings'))

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
            offense_type = request.form.get('offense_type')
            reason = request.form.get('reason')
            offense_date = request.form.get('offense_date')
            decision_date = request.form.get('decision_date')
            expiry_date = request.form.get('expiry_date')
            approved_by = request.form.get('approved_by')
            description = request.form.get('description', '')
            local_committee_date = request.form.get('local_committee_date')
            zone_committee_date = request.form.get('zone_committee_date')
            commission_sent_date = request.form.get('commission_sent_date')
            discipline_status = request.form.get('discipline_status', 'pending')
            
            final_decision = request.form.get('final_decision') if current_user.role == 'admin' else None

            new_record = DisciplineRecord(
                employee_id=emp.id,
                penalty_type=penalty_type,
                offense_type=offense_type,
                reason=reason,
                offense_date=offense_date,
                reporting_date=None,
                decision_date=decision_date,
                effective_date=None,
                expiry_date=expiry_date,
                approved_by=approved_by,
                description=description,
                local_committee_date=local_committee_date,
                zone_committee_date=zone_committee_date,
                commission_sent_date=commission_sent_date,
                discipline_status=discipline_status,
                final_decision=final_decision
            )
            db.session.add(new_record)
            
            log_entry = AuditLog(
                user_id=current_user.id,
                action="Naamusa Galche",
                details=f"Hojjetaaf {emp.full_name} galmeen naamusa ({penalty_type}) galmaa'eera."
            )
            db.session.add(log_entry)

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
        approval_reason = request.form.get('approval_reason')
        
        if status:
            transfer.status = status
        if approval_reason is not None:
            transfer.approval_reason = approval_reason
            
        if status == 'Approved' and transfer.employee and transfer.to_branch_id:
            transfer.employee.branch_id = transfer.to_branch_id

        log_entry = AuditLog(
            user_id=current_user.id,
            action="Jijjiirraa Raggaasise",
            details=f"Hojjetaa {transfer.employee.full_name} jijjiirraan isaa {status} ta'eera."
        )
        db.session.add(log_entry)

        db.session.commit()
        flash("Murtiin jijjiirraa milkaa'inaan galmaa'eera!", 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Dogoggorri uumameera: {str(e)}', 'danger')
    return redirect(url_for('transfers'))

@app.route('/approve_promotion/<int:id>', methods=['POST'])
@login_required
def approve_promotion(id):
    transfer = Transfer.query.get_or_404(id)
    user_b_val = int(current_user.branch_id) if current_user.branch_id and str(current_user.branch_id).isdigit() else current_user.branch_id
    if current_user.role != 'admin' and transfer.employee and transfer.employee.branch_id != user_b_val:
        abort(403)
        
    try:
        create_local_backup()
        transfer.status = 'Approved'
        
        log_entry = AuditLog(
            user_id=current_user.id,
            action="Gonfoo Raggaasise",
            details=f"Hojjetaa {transfer.employee.full_name} gaaffiin gonfoo ragga'eera."
        )
        db.session.add(log_entry)

        db.session.commit()
        flash("Gaaffiin Gonfoo milkaa'inaan ragga'eera (Approved)!", 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Dogoggorri uumameera: {str(e)}', 'danger')
        
    return redirect(url_for('promotions'))

@app.route('/reject_promotion/<int:id>', methods=['POST'])
@login_required
def reject_promotion(id):
    transfer = Transfer.query.get_or_404(id)
    user_b_val = int(current_user.branch_id) if current_user.branch_id and str(current_user.branch_id).isdigit() else current_user.branch_id
    if current_user.role != 'admin' and transfer.employee and transfer.employee.branch_id != user_b_val:
        abort(403)
        
    try:
        create_local_backup()
        transfer.status = 'Rejected'
        
        log_entry = AuditLog(
            user_id=current_user.id,
            action="Gonfoo Dhorke",
            details=f"Hojjetaa {transfer.employee.full_name} gaaffiin gonfoo dhorkameera."
        )
        db.session.add(log_entry)

        db.session.commit()
        flash("Gaaffiin Gonfoo dhorkameera (Rejected)!", 'warning')
    except Exception as e:
        db.session.rollback()
        flash(f'Dogoggorri uumameera: {str(e)}', 'danger')
        
    return redirect(url_for('promotions'))

@app.route('/delete_promotion/<int:id>', methods=['POST'])
@login_required
def delete_promotion(id):
    transfer = Transfer.query.get_or_404(id)
    user_b_val = int(current_user.branch_id) if current_user.branch_id and str(current_user.branch_id).isdigit() else current_user.branch_id
    if current_user.role != 'admin' and transfer.employee and transfer.employee.branch_id != user_b_val:
        abort(403)
        
    try:
        create_local_backup()
        db.session.delete(transfer)
        db.session.commit()
        flash("Gaaffiin Gonfoo tarree irraa haqameera!", 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Dogoggorri uumameera: {str(e)}', 'danger')
        
    return redirect(url_for('promotions'))

@app.route('/add_transfer', methods=['POST'])
@login_required
def add_transfer():
    try:
        create_local_backup()
        employee_id = request.form.get('employee_id')
        to_branch_id = request.form.get('to_branch_id')
        reason = request.form.get('reason')
        transfer_date = request.form.get('transfer_date') or request.form.get('date')

        if not employee_id or not to_branch_id:
            flash('Hojjetaa fi Dameen haaraan dirqama guutamuu qabu!', 'danger')
            return redirect(url_for('transfers'))

        emp = Employee.query.get_or_404(int(employee_id))
        from_branch_id = emp.branch_id

        new_transfer = Transfer(
            employee_id=emp.id,
            from_branch_id=from_branch_id,
            to_branch_id=int(to_branch_id) if str(to_branch_id).isdigit() else None,
            reason=reason,
            transfer_date=transfer_date,
            status='Pending'
        )
        db.session.add(new_transfer)
        
        log_entry = AuditLog(
            user_id=current_user.id,
            action="Gaaffii Jijjiirraa Dhiyeesse",
            details=f"Hojjetaaf {emp.full_name} gaaffiin jijjiirraa dhiyaateera."
        )
        db.session.add(log_entry)

        db.session.commit()
        flash("Gaaffiin jijjiirraa milkaa'inaan dhiyaateera, amma Admin hayyamuu isaa eeggachaa jira!", 'success')
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
        
        log_entry = AuditLog(
            user_id=current_user.id,
            action="Hojjetaa Haaraa Galche",
            details=f"Maqaa hojjetaa: {full_name}, ID: {unique_id}"
        )
        db.session.add(log_entry)

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
            emp.perf_score = float(request.form.get('performance_score', 0) or 0)
            emp.edu_score = float(request.form.get('education_score', 0) or 0)
            emp.discipline_score = float(request.form.get('discipline_score', 0) or 0)
            emp.law_score = float(request.form.get('law_score', 0) or 0)
            emp.experience_score = float(request.form.get('experience_score', 0) or 0)
            emp.service_score = float(request.form.get('service_delivery_score', 0) or 0)
            
            emp.total_score = (emp.perf_score + emp.edu_score + emp.discipline_score + 
                               emp.law_score + emp.experience_score + emp.service_score)
            
            emp.next_promotion_date = request.form.get('next_promotion_date')
            emp.next_promotion_status = request.form.get('next_promotion_status')
            
            if emp.next_promotion_status:
                new_promotion = Transfer(
                    employee_id=emp.id,
                    from_branch_id=emp.branch_id,
                    to_branch_id=emp.branch_id,
                    reason=f'Gaaffii Gonfoo: {emp.next_promotion_status}',
                    transfer_date=emp.next_promotion_date,
                    status='Pending'
                )
                db.session.add(new_promotion)
            
            db.session.commit()
            flash("Qabxiin madaallii hojjetaa fi gaaffiin gonfoo milkaa'inaan galmaa'eera!", 'success')
            return redirect(url_for('promotions'))
        except Exception as e:
            db.session.rollback()
            flash(f'Dogoggorri uumameera: {str(e)}', 'danger')

    return render_template('evaluate_promotion.html', employee=emp)

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
    page = request.args.get('page', 1, type=int)
    per_page = 50

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

    pagination = query.order_by(Employee.full_name.asc()).paginate(page=page, per_page=per_page, error_out=False)
    all_employees = pagination.items

    all_branches = Branch.query.all() if current_user.role == 'admin' else Branch.query.filter_by(id=current_user.branch_id).all()
    all_ranks = Rank.query.all()
    
    return render_template('employees.html', employees=all_employees, pagination=pagination, branches=all_branches, ranks=all_ranks)

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
    rank_id_filter = request.args.get('rank_id')
    
    all_branches = Branch.query.all()
    all_ranks = Rank.query.all()
    
    query = Transfer.query.join(Employee, Transfer.employee_id == Employee.id).filter(Transfer.reason.ilike('%Gaaffii Gonfoo%'))
    
    if status_filter and status_filter != 'All':
        query = query.filter(Transfer.status == status_filter)

    if rank_id_filter and str(rank_id_filter).strip().isdigit():
        query = query.filter(Employee.rank_id == int(rank_id_filter))

    if current_user.role == 'admin':
        if branch_id_filter and str(branch_id_filter).strip().isdigit():
            b_id_int = int(branch_id_filter)
            query = query.filter(
                db.or_(Employee.branch_id == b_id_int, Transfer.to_branch_id == b_id_int)
            )
        promotions_list = query.all()
    else:
        user_b = current_user.branch_id
        if user_b:
            b_val = int(user_b) if str(user_b).isdigit() else user_b
            query = query.filter(Employee.branch_id == b_val)
        else:
            query = query.filter(False)
        promotions_list = query.all()

    return render_template('promotions.html', 
                           promotions=promotions_list, 
                           all_branches=all_branches, 
                           all_ranks=all_ranks,
                           selected_branch=branch_id_filter, 
                           selected_status=status_filter,
                           selected_rank=rank_id_filter)

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

    data = []
    if emps:
        for idx, e in enumerate(emps, start=1):
            branch_name = e.branch.name if e.branch else 'N/A'
            rank_name = e.rank.name if e.rank else 'N/A'
            emp_age = calculate_age(e.birth_date)
            
            data.append({
                'Lakk.': idx,
                'ID Addaa': e.unique_id if e.unique_id else '-',
                'Gulantaa / Rank': rank_name,
                'Maqaa Guutuu': e.full_name,
                'Saala': e.gender if e.gender else '-',
                'Umrii': emp_age,
                'Guyyaa Dhalootaa': format_ethiopian_date(e.birth_date) if e.birth_date else '-',
                'Guyyaa Qacaramuu': format_ethiopian_date(e.hire_date) if e.hire_date else '-',
                'Hanga Tajaajilaa': calculate_service_duration(e.hire_date),
                'Guyyaa Gulantaa': format_ethiopian_date(getattr(e, 'rank_date', None)) if getattr(e, 'rank_date', None) else '-',
                'Damee (Branch)': branch_name,
                'Gita Hojii': e.job_position if e.job_position else '-',
                'Sadarkaa Barumsaa': e.education_level if e.education_level else '-',
                'Gosa Barumsaa': e.field_of_study if e.field_of_study else '-',
                'Mindaa Gulantaa': e.rank_salary if e.rank_salary is not None else 0.0,
                'Kaffaltii Iddoo': e.location_allowance if e.location_allowance is not None else 0.0,
                'Durgoo Nyaataa': getattr(e, 'food_allowance', 0.0) if getattr(e, 'food_allowance', None) is not None else 0.0,
                'Lakk. Sooromaa': getattr(e, 'pension_number', '-') if getattr(e, 'pension_number', None) else '-',
                'Lakk. Bilbilaa': getattr(e, 'phone_number', '-') if getattr(e, 'phone_number', None) else '-',
                'Status': e.status if e.status else '-'
            })
        df = pd.DataFrame(data)
    else:
        df = pd.DataFrame(columns=[
            'Lakk.', 'ID Addaa', 'Gulantaa / Rank', 'Maqaa Guutuu', 'Saala', 'Umrii', 'Guyyaa Dhalootaa', 
            'Guyyaa Qacaramuu', 'Hanga Tajaajilaa', 'Guyyaa Gulantaa', 'Damee (Branch)', 'Gita Hojii', 
            'Sadarkaa Barumsaa', 'Gosa Barumsaa', 'Mindaa Gulantaa', 
            'Kaffaltii Iddoo', 'Durgoo Nyaataa', 'Lakk. Sooromaa', 'Lakk. Bilbilaa', 'Status'
        ])
        
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

@app.route('/export_promotions_excel')
@login_required
def export_promotions_excel():
    branch_id = request.args.get('branch_id')
    status_filter = request.args.get('status', 'Pending')
    rank_id_filter = request.args.get('rank_id')

    query = Transfer.query.join(Employee, Transfer.employee_id == Employee.id).filter(Transfer.reason.ilike('%Gaaffii Gonfoo%'))

    if status_filter and status_filter != 'All':
        query = query.filter(Transfer.status == status_filter)

    if rank_id_filter and str(rank_id_filter).strip().isdigit():
        query = query.filter(Employee.rank_id == int(rank_id_filter))

    if current_user.role == 'admin':
        if branch_id and str(branch_id).strip().isdigit():
            b_id_int = int(branch_id)
            query = query.filter(
                db.or_(Employee.branch_id == b_id_int, Transfer.to_branch_id == b_id_int)
            )
        promotions_list = query.all()
    else:
        user_b = current_user.branch_id
        if user_b:
            b_val = int(user_b) if str(user_b).isdigit() else user_b
            query = query.filter(Employee.branch_id == b_val)
        else:
            query = query.filter(False)
        promotions_list = query.all()

    if not promotions_list:
        flash("Odeeffannoon gaaffii gonfoo filatame waan hin jirreef, Excel-tti buufachuun hin danda'amu!", 'warning')
        return redirect(url_for('promotions', branch_id=branch_id, status=status_filter, rank_id=rank_id_filter))

    data = []
    for idx, p in enumerate(promotions_list, start=1):
        emp = p.employee
        branch_name = '-'
        if emp and emp.branch:
            branch_name = emp.branch.name
        elif p.to_branch_id:
            b_obj = Branch.query.get(p.to_branch_id)
            if b_obj:
                branch_name = b_obj.name

        data.append({
            'Lakk.': idx,
            'Gonfa Ammaa Qabu': emp.rank.name if emp and emp.rank else '-',
            'Maqaa Miseensotaa': emp.full_name if emp else 'N/A',
            'Bakka Hojii': branch_name,
            'Gahee Hojii': emp.job_position if emp and emp.job_position else '-',
            'Saala': emp.gender if emp and emp.gender else '-',
            'Umrii': calculate_age(emp.birth_date) if emp and emp.birth_date else '-',
            'Bara Gonfaa Dura Yeroo Itti Argate': format_ethiopian_date(emp.rank_date) if emp and emp.rank_date else '-',
            'Gonfaa Itti Aanu Yeroo Itti Argatu': format_ethiopian_date(emp.next_promotion_date) if emp and emp.next_promotion_date else (p.transfer_date.strftime('%Y-%m-%d') if p.transfer_date else '-'),
            'Sadarkaa Barumsaa': emp.education_level if emp and emp.education_level else '-',
            'Gosa Barumsaa': emp.field_of_study if emp and emp.field_of_study else '-',
            "Bu'uura Raawwii Hojii (25%)": emp.perf_score if emp and emp.perf_score is not None else 0.0,
            'Sadarkaa Barumsaa (20%)': emp.edu_score if emp and emp.edu_score is not None else 0.0,
            'Naamusaa Poolisii (20%)': emp.discipline_score if emp and emp.discipline_score is not None else 0.0,
            'Seera fi Heera (10%)': emp.law_score if emp and emp.law_score is not None else 0.0,
            'Muxannoo Hojii (10%)': emp.experience_score if emp and emp.experience_score is not None else 0.0,
            'Mira Tajaajiltummaa (15%)': emp.service_score if emp and emp.service_score is not None else 0.0,
            'Ida\'amaa': f"{emp.total_score if emp and emp.total_score is not None else 0.0}%",
            'Gonfoo Itti Guddatuu': emp.next_promotion_status if emp and emp.next_promotion_status else '-',
            'Haala (Status)': getattr(p, 'status', '-')
        })

    if not data:
        flash("Odeeffannoon export ta'u tokkollee hin argamne!", 'warning')
        return redirect(url_for('promotions', branch_id=branch_id, status=status_filter, rank_id=rank_id_filter))

    df = pd.DataFrame(data)
    output = io.BytesIO()
    
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Gaaffii Gonfoo Madaallii')
    
    output.seek(0)

    return send_file(
        output, 
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', 
        as_attachment=True, 
        download_name='Gaaffii_Gonfoo_Madaallii_Report.xlsx'
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
        
        log_entry = AuditLog(
            user_id=current_user.id,
            action="Fayyadamaa Uumame",
            details=f"Fayyadamaan {username} ({role}) uumameera."
        )
        db.session.add(log_entry)

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