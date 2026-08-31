from flask import Flask, render_template, request, jsonify
from flask_sqlalchemy import SQLAlchemy

# Kuni dirqama app jedhamuun barreeffamuu qaba!
app = Flask(__name__)

# Database Configuration (Fakkeenyaaf Supabase / PostgreSQL)
app.config['SQLALCHEMY_DATABASE_URI'] = 'YOUR_DATABASE_URL_HERE'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# --- Routes fi Models kee asitti galchita ---

@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)