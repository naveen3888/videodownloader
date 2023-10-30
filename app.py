from flask import Flask, render_template, request, redirect, session, flash, url_for,send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
import os
import yt_dlp




app = Flask(__name__)
app.secret_key = 'your_secret_key_1284732472'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(60))

    def __init__(self, email, password, name):
        self.email = email
        self.password = bcrypt.generate_password_hash(password).decode('utf-8')
        self.name = name

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']

        user = User(email=email, password=password, name=name)
        db.session.add(user)
        db.session.commit()
        flash('Registration successful. You can now log in.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email).first()

        if user and bcrypt.check_password_hash(user.password, password):
            session['user_id'] = user.id
            return redirect(url_for('dashboard'))
        else:
            flash('Login failed. Please check your email and password.', 'danger')

    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if 'user_id' in session:
        user = User.query.filter_by(id=session['user_id']).first()
        if user:
            return render_template('dashboard.html', user=user)
        else:
            flash('User not found', 'danger')
            return redirect('/login')
    else:
        flash('Please log in to access the dashboard.', 'warning')
        return redirect('/login')

def remove_files_on_session_end(user_session_folder):
    folder_path = os.path.join("static", user_session_folder)
    for file_name in os.listdir(folder_path):
        file_path = os.path.join(folder_path, file_name)
        os.remove(file_path)

'''@app.route('/logout')
def logout():
    session.pop('user_id', None)
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))'''

@app.route('/logout')
def logout():
    user_id = session.pop('user_id', None)
    if user_id:
        user_session_folder = f"user_{user_id}"
        folder_path = os.path.join("static", user_session_folder)
        try:
            for file_name in os.listdir(folder_path):
                file_path = os.path.join(folder_path, file_name)
                os.remove(file_path)
            flash('Files have been removed from the static folder.', 'info')
        except Exception as e:
            flash(f'Error removing files: {str(e)}', 'danger')
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))





# Define info_dict at a broader scope, outside of the functions
info_dict = None

@app.route('/video_downloader', methods=['GET', 'POST'])
def video_downloader():
    if request.method == 'POST':
        youtube_url = request.form['youtube_url']
        download_type = request.form['download_type']

        try:
            if download_type == 'audio':
                ydl_opts = {
                    'format': 'bestaudio/best',
                    'outtmpl': 'static/%(title)s.%(ext)s',  # Save audio as .webm
                }
            else:
                ydl_opts = {
                    'format': 'best',
                    'outtmpl': 'static/%(title)s.%(ext)s',
                }
            ydl = yt_dlp.YoutubeDL(ydl_opts)
            info_dict = ydl.extract_info(youtube_url, download=True)
            
            # Store video title in the session
            session['title'] = info_dict.get('title', 'Video')
            
            if download_type == 'audio':
                flash("Audio has been downloaded in the original format.")
                return redirect(url_for('download', download_type=download_type))
            else:
                return redirect(url_for('download', download_type=download_type))
        except Exception as e:
            return f"An error occurred: {str(e)}"

    return render_template('video_downloader.html')




@app.route('/download/<download_type>')
def download(download_type):
    video_title = session.get('title')  # Retrieve the video title from the session

    if download_type == 'audio':
        return render_template('download.html', video_title=video_title, download_type=download_type)
    else:
        return render_template('download.html', video_title=video_title, download_type=download_type)



if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', debug=True)
