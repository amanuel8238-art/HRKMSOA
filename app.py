@app.route('/api/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')

        if not db:
            return jsonify({"success": False, "message": "Database connection error!"}), 500

        # Username database irraa barbaaduu
        result = db.session.execute(db.text('SELECT * FROM users WHERE username = :uname'), {'uname': username})
        user = result.mappings().first()

        if not user:
            return jsonify({"success": False, "message": "Maqaa fayyadamaa dogoggoraati!"}), 401

        stored_password = user['password']
        
        # Checking password (Plain text ykn Hashed ta'uu isaa ilaaluun)
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