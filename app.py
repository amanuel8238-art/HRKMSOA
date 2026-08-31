import os
from flask import Flask, render_template, request, jsonify
from flask_sqlalchemy import SQLAlchemy

# Flask app jalqabsiisuu
app = Flask(__name__)

# Database Configuration (Yeroo Localhost ykn Render irratti fayyadamtu)
# Render irratti Database URL Environment Variable irraa fudhata, yoo dhabame immoo sqlite fayyadama
database_url = os.environ.get('DATABASE_URL')
if database_url and database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)

app.config['SQLALCHEMY_DATABASE_URI'] = database_url or 'sqlite:///hrkmso.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# --- Database Models ---
class Employee(db.Model):
    __tablename__ = 'employees'
    
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(100), nullable=False)
    gender = db.Column(db.String(20), nullable=False)
    branch = db.Column(db.String(100), nullable=False)
    position = db.Column(db.String(100), nullable=False)
    rank = db.Column(db.String(50), nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "full_name": self.full_name,
            "gender": self.gender,
            "branch": self.branch,
            "position": self.position,
            "rank": self.rank
        }

# --- Routes (Endpoints) ---

@app.route('/')
def index():
    return render_template('index.html')

# Hojjetoota argachuufi (GET) fi Hojjetaa haaraa galchuuf (POST)
@app.route('/api/employees', methods=['GET', 'POST'])
def handle_employees():
    if request.method == 'POST':
        data = request.get_json()
        new_emp = Employee(
            full_name=data.get('full_name'),
            gender=data.get('gender'),
            branch=data.get('branch'),
            position=data.get('position'),
            rank=data.get('rank')
        )
        db.session.add(new_emp)
        db.session.commit()
        return jsonify({"message": "Hojjetaan haaraan milkaa'inaan galmeeffameera!", "employee": new_emp.to_dict()}), 201
    
    employees = Employee.query.all()
    return jsonify([emp.to_dict() for emp in employees])

# --- Database Tables uumuu ---
with app.app_context():
    db.create_all()

# --- Server Kaasuu (Render Port & Local Support) ---
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=False)