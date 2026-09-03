import os
from flask import Flask, jsonify, render_template, request
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

# Database configuration with safe fallback
database_url = os.environ.get("DATABASE_URL")
if not database_url:
  database_url = "postgresql://postgres.jspbjzjutnwidvsoayna:Ame_2018%23Strong!9X@aws-0-eu-west-1.pooler.supabase.com:5432/postgres"

if database_url and database_url.startswith("postgres://"):
  database_url = database_url.replace("postgres://", "postgresql://", 1)

app.config["SQLALCHEMY_DATABASE_URI"] = database_url
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)


class Employee(db.Model):
  __tablename__ = "employees"

  id = db.Column(db.Integer, primary_key=True)
  full_name = db.Column(db.String(150), nullable=False)
  gender = db.Column(db.String(20), nullable=True)
  birth_date = db.Column(db.String(20), nullable=True)  # Age 55 tracking
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
  db.create_all()


@app.route("/")
def index():
  return render_template("index.html")


@app.route("/api/employees", methods=["GET"])
def get_employees():
  employees = Employee.query.all()
  return jsonify([e.to_dict() for e in employees])


@app.route("/api/employees", methods=["POST"])
def add_employee():
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
          {"message": "Employee added successfully!", "employee": new_emp.to_dict()}
      ),
      201,
  )


if __name__ == "__main__":
  app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))