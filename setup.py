from app import app, db, User, Branch

with app.app_context():
    # Damee Dadar uumuu
    b = Branch(name="Dadar Branch")
    db.session.add(b)
    db.session.commit()
    
    # Admin User uumuu
    admin = User(username="admin", role="admin", branch_id=b.id)
    admin.password = "admin123"
    db.session.add(admin)
    db.session.commit()
    print("Admin fi Branch milkaa'inaan uumamaniiru!")