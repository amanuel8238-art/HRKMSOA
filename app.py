import os
from flask import Flask, jsonify, render_template, request
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

# Direct database connection string with SSL mode for Supabase
database_url = "postgresql://postgres.jspbjzjutnwidvsoayna:Ame_2018%23Strong!9X@aws-0-eu-west-1.pooler.supabase.com:5432/postgres?sslmode=require"

app.config["SQLALCHEMY_DATABASE_URI"] = database_url
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)


class Employee(db.Model):
    __tablename__ = "employees"

    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(150), nullable=False)
    gender = db.Column(db.String(20), nullable=True)
    birth_date = db.Column(db.String(20), nullable=True)
    branch = db.Column(db.String(100), nullable=False)
    rank = db.Column(db.String(100), nullable=False)
    salary = db.Column(db.Float, nullable=True)
    hire_date = db.Column(db.String(20), nullable=True)

    def to_dict(self):
        return {
            "id": self.id,
            "full_name": self.full_name,
            "gender": self.gender,
            "birth_date": self.birth_date,
            "branch": self.branch,
            "rank": self.rank,
            "salary": self.salary,
            "hire_date": self.hire_date,
        }


with app.app_context():
    try:
        db.create_all()
        print("Database tables created successfully!")
    except Exception as e:
        print(f"Database connection error: {e}")


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/employees", methods=["GET"])
def get_employees():
    try:
        employees = Employee.query.all()
        return jsonify([e.to_dict() for e in employees])
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/employees", methods=["POST"])
def add_employee():
    try:
        data = request.json
        new_emp = Employee(
            full_name=data.get("full_name"),
            gender=data.get("gender"),
            birth_date=data.get("birth_date"),
            branch=data.get("branch"),
            rank=data.get("rank"),
            salary=data.get("salary"),
            hire_date=data.get("hire_date"),
        )
        db.session.add(new_emp)
        db.session.commit()
        return (
            jsonify(
                {
                    "message": "Employee added successfully!",
                    "employee": new_emp.to_dict(),
                }
            ),
            201,
        )
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))