# API Route: Members fiduuf (GET) fi Galchuuf (POST)
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
            return jsonify([]), 200  # Error yoo uumame appiin akka hin cinneef empty array deebisa

    elif request.method == 'POST':
        try:
            data = request.get_json()
            response = supabase.table('members').insert(data).execute()
            return jsonify({"success": True, "message": "Miseensi milkaa'inaan galmaa'e!", "data": response.data}), 201
        except Exception as e:
            return jsonify({"success": False, "message": str(e)}), 500

# API Route: Users fiduuf (GET) fi Uumuuf (POST)
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
            return jsonify([]), 200  # Error yoo uumame appiin akka hin cinneef empty array deebisa

    elif request.method == 'POST':
        try:
            data = request.get_json()
            if 'password' in data and data['password']:
                data['password'] = generate_password_hash(data['password'])
                
            response = supabase.table('users').insert(data).execute()
            return jsonify({"success": True, "message": "User milkaa'inaan uumame!", "data": response.data}), 201
        except Exception as e:
            return jsonify({"success": False, "message": str(e)}), 500