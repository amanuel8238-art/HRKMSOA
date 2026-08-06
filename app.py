import os
from flask import Flask, render_template_string, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.secret_key = 'hrkmso_secret_key_secure'

# Database URL kallattiin Supabase (Port 5432 - Session Mode)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres.jspbjzjutnwidvsoayna:Ame_2018%23Strong!9X@aws-0-eu-west-1.pooler.supabase.com:5432/postgres'
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
        
        dadar_branch = Branch.query.filter_by(name='Dadar').first()
        if not dadar_branch:
            db.session.add(Branch(name='Dadar'))
            db.session.commit()
    except Exception as e:
        print(f"DB Init Error: {e}")

# ==================== LOGIN ROUTE ====================
@app.route('/login', methods=['GET', 'POST'])
def login():
    error_msg = ""
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
                error_msg = "Maqaa fayyadamaa ykn jecha darbii dogoggoraati!"
        except Exception as e:
            error_msg = f"Login Error: {str(e)}"
            
    return render_template_string('''
    <!DOCTYPE html>
    <html lang="om">
    <head>
        <meta charset="UTF-8">
        <title>HRKMSO - Seensa (Login)</title>
        <style>
            body { font-family: Arial, sans-serif; background: #f4f6f9; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }
            .login-box { background: white; padding: 30px; border-radius: 8px; box-shadow: 0 4px 10px rgba(0,0,0,0.1); width: 300px; }
            h2 { text-align: center; color: #333; }
            input { width: 100%; padding: 10px; margin: 10px 0; border: 1px solid #ccc; border-radius: 4px; box-sizing: border-box; }
            button { width: 100%; padding: 10px; background: #007bff; color: white; border: none; border-radius: 4px; cursor: pointer; font-size: 16px; }
            button:hover { background: #0056b3; }
            .error { color: red; font-size: 14px; text-align: center; }
        </style>
    </head>
    <body>
        <div class="login-box">
            <h2>HRKMSO Login</h2>
            {% if error_msg %}<div class="error">{{ error_msg }}</div>{% endif %}
            <form method="POST">
                <input type="text" name="username" placeholder="Maqaa Fayyadamaa (Username)" required>
                <input type="password" name="password" placeholder="Jecha Darbii (Password)" required>
                <button type="submit">Seeni</button>
            </form>
            <p style="font-size: 12px; color: #666; text-align: center; margin-top: 15px;">Default Admin: admin / password123</p>
        </div>
    </body>
    </html>
    ''', error_msg=error_msg)

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
        selected_education = request.args.get('education_level')
        selected_rank = request.args.get('rank')
        
        query = Employee.query
        if current_branch and current_branch != 'Head Office':
            query = query.filter_by(branch_name=current_branch)
        else:
            selected_branch = request.args.get('branch')
            if selected_branch and selected_branch != 'Head Office':
                query = query.filter_by(branch_name=selected_branch)
            
        if selected_education:
            query = query.filter(Employee.education_level.ilike(f"%{selected_education}%"))

        if selected_rank:
            query = query.filter(Employee.rank.ilike(f"%{selected_rank}%"))
            
        employees = query.all()
        branches = Branch.query.all()
        
        return render_template_string('''
        <!DOCTYPE html>
        <html lang="om">
        <head>
            <meta charset="UTF-8">
            <title>HRKMSO - Dashboard</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 0; padding: 20px; background: #f4f6f9; }
                .header { background: #007bff; color: white; padding: 15px; border-radius: 5px; display: flex; justify-content: space-between; align-items: center; }
                .container { margin-top: 20px; }
                table { width: 100%; border-collapse: collapse; background: white; margin-top: 15px; }
                th, td { border: 1px solid #ddd; padding: 10px; text-align: left; }
                th { background: #f2f2f2; }
                .form-box { background: white; padding: 20px; border-radius: 5px; margin-bottom: 20px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }
                .filter-box { background: #e9ecef; padding: 15px; border-radius: 5px; margin-bottom: 20px; }
                input, select { padding: 8px; margin: 5px; width: 200px; }
                button { padding: 8px 15px; background: #28a745; color: white; border: none; border-radius: 4px; cursor: pointer; }
                a.logout { color: white; background: #dc3545; padding: 8px 12px; text-decoration: none; border-radius: 4px; }
            </style>
        </head>
        <body>
            <div class="header">
                <h2>Komishinii Manneen Sirreessaa (HRKMSO)</h2>
                <div>
                    <span>Damee: <b>{{ current_branch }}</b></span> | 
                    <a href="/logout" class="logout">Baahi (Logout)</a>
                </div>
            </div>

            <div class="container">
                <!-- Filter Section -->
                <div class="filter-box">
                    <h3>Gabaasa / Filter Gochuu</h3>
                    <form method="GET" action="/">
                        {% if current_branch == 'Head Office' %}
                        <select name="branch">
                            <option value="">Damee Hundaa (All Branches)</option>
                            <option value="Dadar" {% if request.args.get('branch') == 'Dadar' %}selected{% endif %}>Dadar</option>
                            {% for b in branches %}
                                {% if b.name != 'Dadar' and b.name != 'Head Office' %}
                                <option value="{{ b.name }}" {% if request.args.get('branch') == b.name %}selected{% endif %}>{{ b.name }}</option>
                                {% endif %}
                            {% endfor %}
                        </select>
                        {% endif %}
                        <input type="text" name="education_level" placeholder="Sadarkaa Barnootaa" value="{{ request.args.get('education_level', '') }}">
                        <input type="text" name="rank" placeholder="Gonfoo (Rank)" value="{{ request.args.get('rank', '') }}">
                        <button type="submit" style="background: #17a2b8;">Filter</button>
                        <a href="/" style="padding: 8px 15px; background: #6c757d; color: white; text-decoration: none; border-radius: 4px; display: inline-block;">Reset</a>
                    </form>
                </div>

                <!-- Add Employee Form (Always Visible) -->
                <div class="form-box">
                    <h3>Hojjetaa Haaraa Galchuuf</h3>
                    <form method="POST" action="/add">
                        <input type="text" name="full_name" placeholder="Maqaa Guutuu" required>
                        <input type="text" name="position" placeholder="Qacaroo / Hojii" required>
                        <input type="text" name="rank" placeholder="Gonfoo (Rank)" required>
                        <input type="text" name="education_level" placeholder="Sadarkaa Barnootaa" required>
                        <input type="number" name="age" placeholder="Umrii" required>
                        
                        {% if current_branch == 'Head Office' %}
                        <select name="branch_name" required style="padding: 8px; margin: 5px; width: 216px;">
                            <option value="">Damee Filadhu</option>
                            <option value="Dadar">Dadar</option>
                            {% for b in branches %}
                                {% if b.name != 'Dadar' and b.name != 'Head Office' %}
                                <option value="{{ b.name }}">{{ b.name }}</option>
                                {% endif %}
                            {% endfor %}
                        </select>
                        {% else %}
                        <!-- Branch yoo ta'e koodiin kun branch isaa automatic qabata -->
                        <input type="hidden" name="branch_name" value="{{ current_branch }}">
                        <span style="padding: 8px; display:inline-block;">Damee: <b>{{ current_branch }}</b></span>
                        {% endif %}
                        
                        <button type="submit">Galchi (Save)</button>
                    </form>
                </div>

                <h3>Tarreeffama Hojjettootaa</h3>
                <table>
                    <tr>
                        <th>Maqaa Guutuu</th>
                        <th>Qacaroo</th>
                        <th>Gonfoo</th>
                        <th>Sadarkaa Barnootaa</th>
                        <th>Umrii</th>
                        <th>Damee</th>
                    </tr>
                    {% for emp in employees %}
                    <tr>
                        <td>{{ emp.full_name }}</td>
                        <td>{{ emp.position }}</td>
                        <td>{{ emp.rank }}</td>
                        <td>{{ emp.education_level }}</td>
                        <td>{{ emp.age }}</td>
                        <td>{{ emp.branch_name }}</td>
                    </tr>
                    {% else %}
                    <tr><td colspan="6" style="text-align: center;">Daataan galmaa'e hin jiru.</td></tr>
                    {% endfor %}
                </table>
            </div>
        </body>
        </html>
        ''', employees=employees, branches=branches, current_branch=current_branch)
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
        else:
            return "Odeeffannoon guutuun hin galfamne! Maaloo deebi'ii ilaali."
    except Exception as e:
        return f"SAVE ERROR: {str(e)}"
        
    return redirect(url_for('index'))

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)