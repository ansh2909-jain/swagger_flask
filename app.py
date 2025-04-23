import os
from flask import Flask, render_template, request, jsonify, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv
from flasgger import Swagger, swag_from
from basicauthmiddleware import BasicAuthMiddleware
from models import db, Student

# Load environment variables
load_dotenv()
VALID_USERNAME = os.getenv("username")
VALID_PASSWORD = os.getenv("password")

# Initialize Flask App
app = Flask(__name__)

# Swagger Configuration (initialize once)
app.config['SWAGGER'] = {
    'title': 'Student Management API',
    'uiversion': 3
}

# Initialize Swagger
swagger = Swagger(app, config={
    "headers": [],
    "specs": [
        {
            "endpoint": 'apispec_1',
            "route": '/docs/swagger.json',
            "rule_filter": lambda rule: True,
            "model_filter": lambda tag: True,
        }
    ],
    "static_url_path": "/flasgger_static",  # Make sure static files are served
    "swagger_ui": True,  # Ensures Swagger UI is enabled
    "specs_route": "/docs/"  # Swagger UI will be available at /docs/
})

# Apply Basic Auth Middleware
app.wsgi_app = BasicAuthMiddleware(app.wsgi_app, VALID_USERNAME, VALID_PASSWORD)

# Configure SQLite Database
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'database.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

@app.route("/", methods=["GET"])
@swag_from({
    'responses': {
        302: {
            'description': 'Redirect to students list'
        }
    }
})
def index():
    return redirect(url_for('students'))

@app.route("/hello", methods=["GET"])
@swag_from({
    'responses': {
        200: {
            'description': 'Greets the authenticated user',
            'examples': {
                'application/json': {'message': 'Hello, user!'}
            }
        }
    }
})
def hello():
    user = request.environ.get("user")
    return jsonify(message=f"Hello, {user['name']}! Hope you're doing great!")

@app.route("/goodbye", methods=["GET"])
@swag_from({
    'responses': {
        302: {'description': 'Redirect to students list'}
    }
})
def goodbye():
    return redirect(url_for('students'))

@app.route('/students/', methods=["GET"])
@swag_from({
    'responses': {
        200: {
            'description': 'List all students',
            'schema': {
                'type': 'array',
                'items': {'$ref': '#/definitions/Student'}
            }
        }
    }
})
def students():
    students = Student.query.all()
    return render_template('index.html', students=students)

@app.route('/<int:student_id>/', methods=["GET"])
@swag_from({
    'parameters': [
        {
            'name': 'student_id',
            'in': 'path',
            'required': True,
            'type': 'integer'
        }
    ],
    'responses': {
        200: {
            'description': 'Fetch student details',
            'schema': {'$ref': '#/definitions/Student'}
        },
        404: {
            'description': 'Student not found'
        }
    }
})
def student(student_id):
    student = Student.query.get_or_404(student_id)
    return render_template('student.html', student=student)

@app.route('/<int:student_id>/edit/', methods=['GET', 'POST'])
@swag_from({
    'parameters': [
        {
            'name': 'student_id',
            'in': 'path',
            'required': True,
            'type': 'integer'
        },
        {
            'name': 'firstname',
            'in': 'formData',
            'type': 'string'
        },
        {
            'name': 'lastname',
            'in': 'formData',
            'type': 'string'
        },
        {
            'name': 'email',
            'in': 'formData',
            'type': 'string'
        },
        {
            'name': 'age',
            'in': 'formData',
            'type': 'integer'
        },
        {
            'name': 'bio',
            'in': 'formData',
            'type': 'string'
        }
    ],
    'responses': {
        200: {'description': 'Student updated successfully'},
        302: {'description': 'Redirect to students list'}
    }
})
def edit(student_id):
    student = Student.query.get_or_404(student_id)
    if request.method == 'POST':
        student.firstname = request.form['firstname']
        student.lastname = request.form['lastname']
        student.email = request.form['email']
        student.age = int(request.form['age'])
        student.bio = request.form['bio']
        db.session.commit()
        return redirect(url_for('students'))
    return render_template('edit.html', student=student)

@app.route('/<int:student_id>/delete/', methods=['POST'])
@swag_from({
    'parameters': [
        {
            'name': 'student_id',
            'in': 'path',
            'required': True,
            'type': 'integer'
        }
    ],
    'responses': {
        302: {'description': 'Student deleted and redirected'}
    }
})
def delete(student_id):
    student = Student.query.get_or_404(student_id)
    db.session.delete(student)
    db.session.commit()
    return redirect(url_for('students'))

@app.route('/create/', methods=['GET', 'POST'])
@swag_from({
    'parameters': [
        {
            'name': 'firstname',
            'in': 'formData',
            'required': True,
            'type': 'string'
        },
        {
            'name': 'lastname',
            'in': 'formData',
            'required': True,
            'type': 'string'
        },
        {
            'name': 'email',
            'in': 'formData',
            'required': True,
            'type': 'string'
        },
        {
            'name': 'age',
            'in': 'formData',
            'required': True,
            'type': 'integer'
        },
        {
            'name': 'bio',
            'in': 'formData',
            'required': True,
            'type': 'string'
        }
    ],
    'responses': {
        302: {'description': 'Redirect to student list after creation'}
    }
})
def create():
    if request.method == 'POST':
        student = Student(
            firstname=request.form['firstname'],
            lastname=request.form['lastname'],
            email=request.form['email'],
            age=int(request.form['age']),
            bio=request.form['bio']
        )
        db.session.add(student)
        db.session.commit()
        return redirect(url_for('students'))
    return render_template('create.html')

# Run the Flask application
if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True, port=8000)