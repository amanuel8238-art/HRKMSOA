from flask import Flask, request, jsonify, render_template
import os
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import check_password_hash, generate_password_hash

app = Flask(__name__)

# Direct PostgreSQL Connection String via SQLAlchemy
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres.jspbjzjutnwidvsoayna:Ame_2018%23Strong!9X@aws-0-eu-west-1.pooler.supabase.com:5432/postgres'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

@app.route('/')
def index():
    return render_template('index.html')

# API Route: Members fiduuf (GET) fi Galchuuf (POST)
@app.route('/api/members', methods=['GET', 'POST'])
def handle_members():
    if request.method == 'GET':
        try:
            result = db.session.execute(db.text('SELECT * FROM members'))
            rows = [dict(row._mapping) for row in result]
            return jsonify(rows), 200
        except Exception as e:
            print("SERVER ERROR /api/members:", str(e))
            return jsonify([]), 200

    elif request.method == 'POST':
        try:
            data = request.get_json()
            # Kolomiiwwan fi values dynamic ta'een insert gochuu
            columns = ", ".join(data.keys())
            values_placeholder = ", ".join([f":{k}" for k in data.keys()])
            sql = f"INSERT INTO members ({columns}) VALUES ({values_placeholder})"
            
            db.session.execute(db.text(sql), data)
            db.session.commit()
            return jsonify({"success": True, "message": "Miseensi milkaa'inaan galmaa'e!"}), 201
        except Exception as e:
            db.session.rollback()
            return jsonify({"success": False, "message": str(e)}), 500

# API Route: Users fiduuf (GET) fi Uumuuf (POST)
@app.route('/api/users', methods=['GET', 'POST'])
def handle_users():
    if request.method == 'GET':
        try:
            result = db.session.execute(db.text('SELECT * FROM users'))
            rows = [dict(row._mapping) for row in result]
            return jsonify(rows), 200
        except Exception as e:
            print("SERVER ERROR /api/users:", str(e))
            return jsonify([]), 200

    elif request.method == 'POST':
        try:
            data = request.get_json()
            if 'password' in data and data['password']:
                data['password'] = generate_password_hash(data['password'])
                
            columns = ", ".join(data.keys())
            values_placeholder = ", ".join([f":{k}" for k in data.keys()])
            sql = f"INSERT INTO users ({columns}) VALUES ({values_placeholder})"
            
            db.session.execute(db.text(sql), data)
            db.session.commit()
            return jsonify({"success": True, "message": "User milkaa'inaan uumame!"}), 201
        except Exception as e:
            db.session.rollback()
            return jsonify({"success": False, "message": str(e)}), 500

# API Route: Login gochuuf (POST)
@app.route('/api/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')

        result = db.session.execute(db.text('SELECT * FROM users WHERE username = :uname'), {'uname': username})
        user = result.mappings().first()

        if not user:
            return jsonify({"success": False, "message": "Maqaa fayyadamaa dogoggoraati!"}), 401

        stored_password = user['password']
        is_valid = False
        if stored_password:
            if stored_password == password:
                is_valid = True
            elif stored_password.startswith('scrypt:') or stored_password.startswith('pbkdf2:'):
                is_valid = check_password_hash(stored_password, password)

        if is_valid:
            return jsonify({
                "success": True, 
                "message": "Seensa milkaa'e!", 
                "user": user['username'],
                "role": user.get('role', 'admin'),
                "branch": user.get('branch', '')
            }), 200
        else:
            return jsonify({"success": False, "message": "Jecha darbii dogoggoraati!"}), 401

    except Exception as e:
        print("Dogoggora Login:", str(e))
        return jsonify({"success": False, "message": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)