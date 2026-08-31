from werkzeug.security import check_password_hash, generate_password_hash

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
        stored_password = user['password']
        
        # Password hashed ta'uu fi dhiisuu isaa adda baasuu (Plain text ykn Hashed)
        is_valid = False
        if stored_password.startswith('scrypt:') or stored_password.startswith('pbkdf2:'):
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