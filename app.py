from flask import Flask, render_template, request, redirect, url_for, session, flash
import os
import uuid
from datetime import datetime
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'your-secret-key-change-this'
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max upload

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

# ─── In-memory storage (replace with a database in production) ────────────────
users = {}   # username -> {password, bio, avatar}
posts = []   # list of post dicts


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def get_post_by_id(post_id):
    return next((p for p in posts if p['id'] == post_id), None)


# ─── Auth Routes ──────────────────────────────────────────────────────────────

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password']
        if username in users:
            flash('Username already taken.', 'error')
        elif not username or not password:
            flash('All fields are required.', 'error')
        else:
            users[username] = {'password': password, 'bio': '', 'avatar': None}
            session['user'] = username
            return redirect(url_for('home'))
    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password']
        if username in users and users[username]['password'] == password:
            session['user'] = username
            return redirect(url_for('home'))
        flash('Invalid username or password.', 'error')
    return render_template('login.html')


@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('login'))


# ─── Feed ─────────────────────────────────────────────────────────────────────

@app.route('/')
def home():
    if 'user' not in session:
        return redirect(url_for('login'))
    feed = sorted(posts, key=lambda p: p['created_at'], reverse=True)
    return render_template('home.html', posts=feed, current_user=session['user'])


# ─── Create Post ──────────────────────────────────────────────────────────────

@app.route('/create', methods=['GET', 'POST'])
def create_post():
    if 'user' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        caption = request.form.get('caption', '')
        image = request.files.get('image')

        if not image or not allowed_file(image.filename):
            flash('Please upload a valid image (jpg, png, gif, webp).', 'error')
            return redirect(url_for('create_post'))

        ext = image.filename.rsplit('.', 1)[1].lower()
        filename = f"{uuid.uuid4().hex}.{ext}"
        image.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

        posts.append({
            'id': uuid.uuid4().hex,
            'author': session['user'],
            'image': filename,
            'caption': caption,
            'likes': [],
            'comments': [],
            'created_at': datetime.now()
        })
        return redirect(url_for('home'))

    return render_template('create.html', current_user=session['user'])


# ─── Like ─────────────────────────────────────────────────────────────────────

@app.route('/like/<post_id>', methods=['POST'])
def like_post(post_id):
    if 'user' not in session:
        return redirect(url_for('login'))
    post = get_post_by_id(post_id)
    if post:
        user = session['user']
        if user in post['likes']:
            post['likes'].remove(user)
        else:
            post['likes'].append(user)
    return redirect(request.referrer or url_for('home'))


# ─── Comment ──────────────────────────────────────────────────────────────────

@app.route('/comment/<post_id>', methods=['POST'])
def comment_post(post_id):
    if 'user' not in session:
        return redirect(url_for('login'))
    post = get_post_by_id(post_id)
    text = request.form.get('comment', '').strip()
    if post and text:
        post['comments'].append({
            'author': session['user'],
            'text': text,
            'created_at': datetime.now()
        })
    return redirect(request.referrer or url_for('home'))


# ─── Profile ──────────────────────────────────────────────────────────────────

@app.route('/profile/<username>')
def profile(username):
    if 'user' not in session:
        return redirect(url_for('login'))
    if username not in users:
        flash('User not found.', 'error')
        return redirect(url_for('home'))
    user_posts = [p for p in posts if p['author'] == username]
    user_posts = sorted(user_posts, key=lambda p: p['created_at'], reverse=True)
    return render_template('profile.html',
                           profile_user=username,
                           user_info=users[username],
                           user_posts=user_posts,
                           current_user=session['user'])


# ─── Delete Post ──────────────────────────────────────────────────────────────

@app.route('/delete/<post_id>', methods=['POST'])
def delete_post(post_id):
    if 'user' not in session:
        return redirect(url_for('login'))
    global posts
    post = get_post_by_id(post_id)
    if post and post['author'] == session['user']:
        img_path = os.path.join(app.config['UPLOAD_FOLDER'], post['image'])
        if os.path.exists(img_path):
            os.remove(img_path)
        posts = [p for p in posts if p['id'] != post_id]
    return redirect(url_for('home'))


# ─── Run ──────────────────────────────────────────────────────────────────────

if __name__ == '__main__':
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    app.run(debug=True)
