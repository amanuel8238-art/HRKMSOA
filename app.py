import os
from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.secret_key = 'hrkmso_secret_key'

# Render irratti DATABASE_URL jedhamee waan galfameef, inni achi jiru qabachuuf:
db_url = os.environ.get('DATABASE_URL')

if db_url:
    # Render 'postgres://' deebisa, SQLAlchemy garuu 'postgresql://' gaafata
    if db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql://", 1)
    app.config['SQLALCHEMY_DATABASE_URI'] = db_url
else:
    # Kompiitara kee (Local) irratti yeroo yaaltu SQLite fayyadamuuf
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///hrkmso.db'

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

class Employee(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(100), nullable=False)
    position = db.Column(db.String(100), nullable=False)
    branch = db.Column(db.String(100), nullable=False)

with app.app_context():
    db.create_all()

@app.route('/')
def index():
    try:
        employees = Employee.query.all()
        return render_template('index.html', employees=employees)
    except Exception as e:
        return f"TEMPLATE/DB ERROR: {str(e)}"

@app.route('/add', methods=['POST'])
def add_employee():
    try:
        full_name = request.form.get('full_name')
        position = request.form.get('position')
        branch = request.form.get('branch')
        
        if full_name and position and branch:
            new_emp = Employee(full_name=full_name, position=position, branch=branch)
            db.session.add(new_emp)
            db.session.commit()
    except Exception as e:
        print(f"Error: {e}")
    return redirect(url_for('index'))

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=True)