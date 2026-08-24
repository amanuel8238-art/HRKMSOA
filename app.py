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
            # Supabase yoo hin qindaa'in fakkeenyaaf listii duwwaa deebisa
            return jsonify([]), 200

        # Table 'members' irraa daataa hunda fiduu
        response = supabase.table('members').select("*").execute()
        members_list = response.data if response.data else []
        
        return jsonify(members_list), 200
    except Exception as e:
        print("Dogoggora Fiduu:", str(e))
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)