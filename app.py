from flask import Flask, request, jsonify, render_template
import os
from supabase import create_client, Client

app = Flask(__name__)

# Supabase Credentials (Render Environment Variables irraa fudhata)
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

# Supabase client uumuu (Yoo URL fi Key jiraatan)
supabase: Client = None
if SUPABASE_URL and SUPABASE_KEY:
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

@app.route('/')
def index():
    return render_template('index.html')

# API Route: Login gochuuf (POST)
@app.route('/api/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')

        if not supabase:
            return jsonify({"success": False, "message": "Supabase walquunnamtiin hin qindaa'in!"}), 500

        # Supabase irraa table 'users' keessaa user barbaaduu
        response = supabase.table('users').select("*").eq('username', username).execute()
        users = response.data

        if not users or len(users) == 0:
            return jsonify({"success": False, "message": "Maqaa fayyadamaa dogoggoraati!"}), 401

        user = users[0]
        
        # Password kallattiitti wal bira qabuu (Plain text comparison)
        if user['password'] == password:
            return jsonify({"success": True, "message": "Seensa milkaa'e!", "user": user['username']}), 200
        else:
            return jsonify({"success": False, "message": "Jecha darbii dogoggoraati!"}), 401

    except Exception as e:
        print("Dogoggora Login:", str(e))
        return jsonify({"success": False, "message": str(e)}), 500

# API Route: Miseensa haaraa galmeessee Supabase keessa kaa'uuf (POST)
@app.route('/api/members', methods=['POST'])
def register_member():
    try:
        data = request.get_json()
        
        if not supabase:
            return jsonify({"status": "error", "message": "Supabase walquunnamtiin hin qindaa'in!"}), 500

        # Supabase table 'members' jedhamu keessatti daataa dabaluu
        response = supabase.table('members').insert(data).execute()
        
        return jsonify({"status": "success", "message": "Miseensi milkaa'inaan galmaa'e!", "data": response.data}), 201

    except Exception as e:
        print("Dogoggora:", str(e))
        return jsonify({"status": "error", "message": str(e)}), 500

# API Route: Miseensota hunda Supabase irraa fiduuf (GET)
@app.route('/api/members', methods=['GET'])
def get_members():
    try:
        if not supabase:
            return jsonify([]), 200

        # Table 'members' irraa daataa hunda fiduu
        response = supabase.table('members').select("*").execute()
        members_list = response.data if response.data else []
        
        return jsonify(members_list), 200
    except Exception as e:
        print("Dogoggora Fiduu:", str(e))
        return jsonify({"status": "error", "message": str(e)}), 500

# API Route: Dameewwan hunda fiduuf (GET)
@app.route('/api/branches', methods=['GET'])
def get_branches():
    try:
        if not supabase:
            return jsonify([]), 200

        response = supabase.table('branches').select("*").execute()
        branches_list = response.data if response.data else []
        return jsonify(branches_list), 200
    except Exception as e:
        print("Dogoggora Dameewwan Fiduu:", str(e))
        return jsonify({"status": "error", "message": str(e)}), 500

# API Route: Useroota hunda fiduuf (GET)
@app.route('/api/users', methods=['GET'])
def get_users():
    try:
        if not supabase:
            return jsonify([]), 200

        response = supabase.table('users').select("*").execute()
        users_list = response.data if response.data else []
        return jsonify(users_list), 200
    except Exception as e:
        print("Dogoggora Useroota Fiduu:", str(e))
        return jsonify({"status": "error", "message": str(e)}), 500

# API Route: User haaraa galmeessuuf (POST)
@app.route('/api/users', methods=['POST'])
def register_user():
    try:
        data = request.get_json()
        if not supabase:
            return jsonify({"status": "error", "message": "Supabase walquunnamtiin hin qindaa'in!"}), 500

        response = supabase.table('users').insert(data).execute()
        return jsonify({"status": "success", "message": "User milkaa'inaan galmaa'e!", "data": response.data}), 201
    except Exception as e:
        print("Dogoggora User Galchuu:", str(e))
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)