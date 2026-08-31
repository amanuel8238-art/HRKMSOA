@app.route('/api/members', methods=['GET', 'POST'])
def handle_members():
    if not supabase:
        return jsonify({"success": False, "message": "Supabase connection not configured!"}), 500

    if request.method == 'GET':
        try:
            # Kolomiiwwan amma Supabase irra jiran waliin wal simsiisuun fiduu
            response = supabase.table('members').select("id, name, branch, rank, promotionDate, gender, hireYear, birthYear, rankSalary, status").execute()
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