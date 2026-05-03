from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from flask_cors import CORS
import os, datetime

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///data.db'
app.config['JWT_SECRET_KEY'] = 'secretkey'

db = SQLAlchemy(app)
jwt = JWTManager(app)
CORS(app)

# ---------------- MODELS ----------------

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(200))
    role = db.Column(db.String(20))

class Project(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    created_by = db.Column(db.Integer)

class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200))
    status = db.Column(db.String(50))
    project_id = db.Column(db.Integer)
    assigned_to = db.Column(db.Integer)

# ---------------- AUTH ----------------

@app.route('/signup', methods=['POST'])
def signup():
    data = request.json
    user = User(**data)
    db.session.add(user)
    db.session.commit()
    return jsonify({"msg": "User created"})

@app.route('/login', methods=['POST'])
def login():
    data = request.json
    user = User.query.filter_by(email=data['email'], password=data['password']).first()

    if not user:
        return jsonify({"msg": "Invalid credentials"}), 401

    token = create_access_token(identity=str(user.id), expires_delta=datetime.timedelta(days=1))
    return jsonify({"token": token, "role": user.role})

# ---------------- PROJECT ----------------

@app.route('/projects', methods=['POST'])
@jwt_required()
def create_project():
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)

    if user.role != "admin":
        return jsonify({"msg": "Only admin allowed"}), 403

    data = request.json
    project = Project(name=data['name'], created_by=user_id)
    db.session.add(project)
    db.session.commit()

    return jsonify({"msg": "Project created"})

@app.route('/projects', methods=['GET'])
@jwt_required()
def get_projects():
    projects = Project.query.all()
    return jsonify([{"id": p.id, "name": p.name} for p in projects])

# ---------------- TASK ----------------

@app.route('/tasks', methods=['POST'])
@jwt_required()
def create_task():
    data = request.json
    task = Task(title=data['title'], status="pending", project_id=data['project_id'], assigned_to=data['assigned_to'])
    db.session.add(task)
    db.session.commit()
    return jsonify({"msg": "Task created"})

@app.route('/tasks', methods=['GET'])
@jwt_required()
def get_tasks():
    tasks = Task.query.all()
    return jsonify([{"id": t.id, "title": t.title, "status": t.status} for t in tasks])

@app.route('/tasks/<int:id>', methods=['PUT'])
@jwt_required()
def update_task(id):
    task = Task.query.get(id)
    task.status = request.json['status']
    db.session.commit()
    return jsonify({"msg": "Updated"})

# ---------------- DASHBOARD ----------------

@app.route('/dashboard', methods=['GET'])
@jwt_required()
def dashboard():
    total = Task.query.count()
    completed = Task.query.filter_by(status="completed").count()
    pending = Task.query.filter_by(status="pending").count()

    return jsonify({"total": total, "completed": completed, "pending": pending})

# ---------------- RUN ----------------

with app.app_context():
    db.create_all()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
