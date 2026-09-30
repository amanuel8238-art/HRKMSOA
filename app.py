from flask import Flask, render_template, request, redirect, url_for, flash, Response
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from models import db, User, Branch, Rank, Employee, Transfer, DisciplineRecord, PromotionAssessment
import csv
import io

app = Flask(__name__)
app.config['SECRET_KEY'] = 'hrkmso_secure_secret_key_2026'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///hrkmso.db' 
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

with app.app_context():
    db.create_all()

# --- ROUTES ---

@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        if user and user.password == password:
            login_user(user)
            if user.role == 'head_office':
                return redirect(url_for('head_office_dashboard'))
            else:
                return redirect(url_for('branch_dashboard'))
        flash('Maqaa fayyadamaa ykn jecha icciti Dogoggoraadha!', 'danger')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

# 1. Branch Dashboard
@app.route('/branch/dashboard')
@login_required
def branch_dashboard():
    branch_id = current_user.branch_id
    employees = Employee.query.filter_by(branch_id=branch_id).all()
    ranks = Rank.query.all()
    return render_template('branch_dashboard.html', employees=employees, ranks=ranks)

# 2. Promotion Assessment Form Handler
@app.route('/evaluate/<int:employee_id>', methods=['POST'])
@login_required
def evaluate_employee(employee_id):
    employee = Employee.query.get_or_404(employee_id)
    
    perf = float(request.form.get('performance_score', 0))
    edu = float(request.form.get('education_score', 0))
    disc = float(request.form.get('discipline_score', 0))
    law = float(request.form.get('law_compliance_score', 0))
    exp = float(request.form.get('experience_score', 0))
    serv = float(request.form.get('service_spirit_score', 0))
    
    total = perf + edu + disc + law + exp + serv
    next_rank_id = request.form.get('next_rank_id')
    
    assessment = PromotionAssessment(
        employee_id=employee.id,
        performance_score=perf,
        education_score=edu,
        discipline_score=disc,
        law_compliance_score=law,
        experience_score=exp,
        service_spirit_score=serv,
        total_score=total,
        current_rank_id=employee.rank_id,
        next_rank_id=int(next_rank_id) if next_rank_id else None,
        status='Pending Head Office Review'
    )
    
    db.session.add(assessment)
    db.session.commit()
    flash('Gamaaggamni hojjetichaa milkaa’inaan galmaa’eera!', 'success')
    return redirect(url_for('branch_dashboard'))

# 3. Head Office Dashboard (Damee filatameef sirriitti qindaa'e)
@app.route('/head-office/dashboard')
@login_required
def head_office_dashboard():
    branch_id = request.args.get('branch_id', type=int)
    branches = Branch.query.all()
    
    if branch_id:
        # Sirreeffama join query SQLAlchemy
        assessments = PromotionAssessment.query.join(Employee).filter(Employee.branch_id == branch_id).all()
    else:
        assessments = PromotionAssessment.query.all()
        
    return render_template('head_office_dashboard.html', assessments=assessments, branches=branches, selected_branch=branch_id)

# 4. Head Office Approve Godhuu
@app.route('/head-office/approve/<int:assessment_id>')
@login_required
def approve_assessment(assessment_id):
    assessment = PromotionAssessment.query.get_or_404(assessment_id)
    assessment.status = 'Approved by Head Office'
    
    if assessment.next_rank_id:
        employee = Employee.query.get(assessment.employee_id)
        employee.rank_id = assessment.next_rank_id
        
    db.session.commit()
    flash('Gamaaggamni kun milkaa’inaan mirkanaa’eera (Approved)!', 'success')
    return redirect(url_for('head_office_dashboard'))

# 5. Excel / CSV Export
@app.route('/head-office/export-csv')
@login_required
def export_csv():
    output = io.StringIO()
    writer = csv.writer(output)
    
    writer.writerow([
        'ID', 'Maqaa Guutuu', 'Damee (Branch)', 'Gahee Hojii', 
        'Sadarkaa Barumsaa', 'Gosa Barumsaa', 'Ida\'ama Waliigalaa (%)', 
        'Gonfoo Ammaa', 'Gonfoo Itti Aanu', 'Haala (Status)'
    ])
    
    assessments = PromotionAssessment.query.all()
    for a in assessments:
        emp = a.employee
        branch_name = emp.branch.name if emp.branch else 'Hin beekamne'
        current_rank = emp.rank.name if emp.rank else 'Hin beekamne'
        next_rank = a.next_rank.name if a.next_rank else 'Hin beekamne'
        
        writer.writerow([
            emp.id, emp.full_name, branch_name, emp.job_position,
            emp.education_level, emp.field_of_study, a.total_score,
            current_rank, next_rank, a.status
        ])
        
    output.seek(0)
    return Response(
        output,
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment;filename=HRKMSO_Promotion_Evaluations.csv"}
    )

if __name__ == '__main__':
    app.run(debug=True)