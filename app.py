from flask import Flask, request, jsonify, render_template
import os
from supabase import create_client, Client
from werkzeug.security import check_password_hash, generate_password_hash

app = Flask(__name__)

# Supabase Configuration
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

supabase: Client = None
if SUPABASE_URL and SUPABASE_KEY:
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/members', methods=['GET', 'POST'])
def handle_members():
    if not supabase:
        return jsonify({"success": False, "message": "Supabase connection not configured!"}), 500

    if request.method == 'GET':
        try:
            response = supabase.table('members').select("*").execute()
            return jsonify(response.data), 200
        except Exception as e:
            print("SERVER ERROR /api/members:", str(e))
            return jsonify([]), 200

    elif request.method == 'POST':
        try:
            data = request.get_json()
            response = supabase.table('members').insert(data).execute()
            return jsonify({"success": True, "message": "Miseensi milkaa'inaan galmaa'e!", "data": response.data}), 201
        except Exception as e:
            return jsonify({"success": False, "message": str(e)}), 500

@app.route('/api/users', methods=['GET', 'POST'])
def handle_users():
    if not supabase:
        return jsonify({"success": False, "message": "Supabase connection not configured!"}), 500

    if request.method == 'GET':
        try:
            response = supabase.table('users').select("*").execute()
            return jsonify(response.data), 200
        except Exception as e:
            print("SERVER ERROR /api/users:", str(e))
            return jsonify([]), 200

    elif request.method == 'POST':
        try:
            data = request.get_json()
            if 'password' in data and data['password']:
                data['password'] = generate_password_hash(data['password'])
                
            response = supabase.table('users').insert(data).execute()
            return jsonify({"success": True, "message": "User milkaa'inaan uumame!", "data": response.data}), 201
        except Exception as e:
            return jsonify({"success": False, "message": str(e)}), 500

@app.route('/api/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')

        if not supabase:
            return jsonify({"success": False, "message": "Supabase connection not configured!"}), 500

        response = supabase.table('users').select("*").eq('username', username).execute()
        users = response.data

        if not users or len(users) == 0:
            return jsonify({"success": False, "message": "Maqaa fayyadamaa dogoggoraati!"}), 401

        user = users[0]
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