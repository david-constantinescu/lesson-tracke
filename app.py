from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'your_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    surname = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    entries = db.relationship('Entry', backref='owner', lazy=True)
    lessons = db.relationship('Lesson', backref='owner', lazy=True)

class Entry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.String(150), nullable=False)
    class_name = db.Column(db.String(150), nullable=False)
    lesson_title = db.Column(db.String(150), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

class Lesson(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.String(150), nullable=False)
    name = db.Column(db.String(150), nullable=False)
    class_name = db.Column(db.String(150), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            return redirect(url_for('dashboard'))
        flash('Login Unsuccessful. Please check email and password', 'danger')
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        name = request.form['name']
        surname = request.form['surname']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        if password == confirm_password:
            hashed_password = generate_password_hash(password, method='sha256')
            new_user = User(name=name, surname=surname, email=email, password=hashed_password)
            db.session.add(new_user)
            db.session.commit()
            return redirect(url_for('login'))
        flash('Passwords do not match', 'danger')
    return render_template('signup.html')

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user = User.query.get(session['user_id'])
    entries = Entry.query.filter_by(user_id=user.id).all()
    lessons = Lesson.query.filter_by(user_id=user.id).all()
    today = datetime.now().strftime('%Y-%m-%d')
    start_date = datetime(datetime.now().year, 9, 1)  # 1st September of the current year

    # Calculate status for each class
    class_status = {}
    classes = set([lesson.class_name for lesson in lessons] + [entry.class_name for entry in entries])
    
    for class_name in classes:
        scheduled_lessons = [lesson for lesson in lessons if lesson.class_name == class_name and datetime.strptime(lesson.date, '%Y-%m-%d') <= datetime.now()]
        taught_lessons = [entry for entry in entries if entry.class_name == class_name and datetime.strptime(entry.date, '%Y-%m-%d') <= datetime.now()]
        
        scheduled_count = len(scheduled_lessons)
        taught_count = len(taught_lessons)
        
        if taught_count < scheduled_count:
            class_status[class_name] = f"Behind by {scheduled_count - taught_count} lessons"
        elif taught_count > scheduled_count:
            class_status[class_name] = f"Ahead by {taught_count - scheduled_count} lessons"
        else:
            class_status[class_name] = "On track"

    upcoming_lessons = [lesson for lesson in lessons if lesson.date >= today]
    return render_template(
        'dashboard.html',
        entries=entries,
        upcoming_lessons=upcoming_lessons,
        class_status=class_status,
    )

@app.route('/add_entry', methods=['GET', 'POST'])
def add_entry():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    if request.method == 'POST':
        date = request.form['date'] or datetime.now().strftime('%Y-%m-%d')
        class_name = request.form['class_name']
        lesson_title = request.form['lesson_title']
        new_entry = Entry(date=date, class_name=class_name, lesson_title=lesson_title, user_id=session['user_id'])
        db.session.add(new_entry)
        db.session.commit()
        return redirect(url_for('dashboard'))
    return render_template('add_entry.html')

@app.route('/schedule', methods=['GET', 'POST'])
def schedule():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    if request.method == 'POST':
        date = request.form['date']
        name = request.form['lesson_name']
        class_name = request.form['class_name']
        if date and name and class_name:
            new_lesson = Lesson(date=date, name=name, class_name=class_name, user_id=session['user_id'])
            db.session.add(new_lesson)
            db.session.commit()
            return redirect(url_for('dashboard'))
        flash('Please provide a date, lesson name, and class.', 'danger')
    return render_template('schedule.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('index'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Create database tables
    app.run(host='0.0.0.0', port=2209, debug=True)