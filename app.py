from flask import Flask, request, jsonify, render_template
import os
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import check_password_hash, generate_password_hash

app = Flask(__name__)

# SQLAlchemy Configuration with Supabase Pooler
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
            # SQLAlchemy raw SQL ykn model fayyadamuun fiduu
            result = db.session.execute(db.text('SELECT * FROM members'))
            rows = [dict(row._mapping) for row in result]
            return jsonify(rows), 200
        except Exception as e:
            print("SERVER ERROR /api/members:", str(e))
            return jsonify([]), 200

    elif request.method == 'POST':
        try:
            data = request.get_json()
            # Asitti insert logic kee barreessuu dandeessa
            return jsonify({"success": True, "message": "Miseensi milkaa'inaan galmaa'e!"}), 201
        except Exception as e:
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
            return jsonify({"success": True, "message": "User milkaa'inaan uumame!"}), 201
        except Exception as e:
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
        if stored_password and (stored_password.startswith('scrypt:') or stored_password.startswith('pbkdf2:')):
            is_valid = check_password_hash(stored_password, password)
        else:
            is_valid = (stored_password == password)

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