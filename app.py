from flask import Flask, render_template, request, redirect, url_for, session, flash
import os
import uuid
from datetime import datetime, timedelta
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'your-secret-key-change-this'
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

SKILL_TAGS = [
    'Portrait', 'Street Photography', 'Landscape', 'Macro',
    'Long Exposure', 'Bokeh', 'Black & White', 'Wildlife',
    'Architecture', 'Golden Hour', 'Urban', 'Minimalism',
    'Astrophotography', 'Documentary', 'Abstract'
]

# ─── In-memory storage ───────────────────────────────────────────────────────
users      = {}
posts      = []
challenges = [
    {
        'id':          'challenge-001',
        'title':       'Capture Solitude',
        'prompt':      'Show us what solitude looks like through your lens. Empty streets, lone figures, quiet spaces.',
        'week_number': 1,
        'start_date':  datetime.now() - timedelta(days=1),
        'end_date':    datetime.now() + timedelta(days=6),
        'entries':     []
    }
]


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_post_by_id(post_id):
    return next((p for p in posts if p['id'] == post_id), None)

def get_challenge_by_id(cid):
    return next((c for c in challenges if c['id'] == cid), None)

def get_active_challenge():
    now = datetime.now()
    return next((c for c in challenges if c['start_date'] <= now <= c['end_date']), None)


# ─── Auth ────────────────────────────────────────────────────────────────────

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
            users[username] = {
                'password': password, 'bio': '', 'avatar': None,
                'challenge_wins': 0, 'badges': []
            }
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


# ─── Feed ────────────────────────────────────────────────────────────────────

@app.route('/')
def home():
    if 'user' not in session:
        return redirect(url_for('login'))
    feed           = sorted(posts, key=lambda p: p['created_at'], reverse=True)
    active_challenge = get_active_challenge()
    return render_template('home.html', posts=feed,
                           current_user=session['user'],
                           active_challenge=active_challenge)


# ─── Create Post ─────────────────────────────────────────────────────────────

@app.route('/create', methods=['GET', 'POST'])
def create_post():
    if 'user' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        caption   = request.form.get('caption', '')
        tags      = request.form.getlist('tags')          # skill tags
        image     = request.files.get('image')

        if not image or not allowed_file(image.filename):
            flash('Please upload a valid image.', 'error')
            return redirect(url_for('create_post'))

        ext      = image.filename.rsplit('.', 1)[1].lower()
        filename = f"{uuid.uuid4().hex}.{ext}"
        image.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

        posts.append({
            'id':         uuid.uuid4().hex,
            'author':     session['user'],
            'image':      filename,
            'caption':    caption,
            'tags':       tags,
            'likes':      [],
            'comments':   [],
            'created_at': datetime.now()
        })
        return redirect(url_for('home'))

    return render_template('create.html', current_user=session['user'],
                           skill_tags=SKILL_TAGS)


# ─── Like ────────────────────────────────────────────────────────────────────

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


# ─── Comment ─────────────────────────────────────────────────────────────────

@app.route('/comment/<post_id>', methods=['POST'])
def comment_post(post_id):
    if 'user' not in session:
        return redirect(url_for('login'))
    post = get_post_by_id(post_id)
    text = request.form.get('comment', '').strip()
    if post and text:
        post['comments'].append({
            'author':     session['user'],
            'text':       text,
            'created_at': datetime.now()
        })
    return redirect(request.referrer or url_for('home'))


# ─── Profile ─────────────────────────────────────────────────────────────────

@app.route('/profile/<username>')
def profile(username):
    if 'user' not in session:
        return redirect(url_for('login'))
    if username not in users:
        flash('User not found.', 'error')
        return redirect(url_for('home'))
    user_posts = sorted([p for p in posts if p['author'] == username],
                        key=lambda p: p['created_at'], reverse=True)

    # collect all skill tags this user has used
    all_tags = []
    for p in user_posts:
        all_tags.extend(p.get('tags', []))
    skill_summary = list(set(all_tags))

    return render_template('profile.html',
                           profile_user=username,
                           user_info=users[username],
                           user_posts=user_posts,
                           skill_summary=skill_summary,
                           current_user=session['user'])


# ─── Delete Post ─────────────────────────────────────────────────────────────

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


# ─── Challenges ──────────────────────────────────────────────────────────────

@app.route('/challenges')
def challenges_list():
    if 'user' not in session:
        return redirect(url_for('login'))
    now = datetime.now()
    active = [c for c in challenges if c['end_date'] >= now]
    past   = [c for c in challenges if c['end_date'] < now]
    return render_template('challenges.html',
                           active=active, past=past,
                           current_user=session['user'],
                           now=now)


@app.route('/challenges/<challenge_id>')
def challenge_detail(challenge_id):
    if 'user' not in session:
        return redirect(url_for('login'))
    challenge = get_challenge_by_id(challenge_id)
    if not challenge:
        flash('Challenge not found.', 'error')
        return redirect(url_for('challenges_list'))

    user          = session['user']
    already_entered = any(e['author'] == user for e in challenge['entries'])
    now           = datetime.now()
    is_active     = challenge['start_date'] <= now <= challenge['end_date']

    # sort entries by vote count
    sorted_entries = sorted(challenge['entries'],
                            key=lambda e: len(e['votes']), reverse=True)

    return render_template('challenge_detail.html',
                           challenge=challenge,
                           entries=sorted_entries,
                           current_user=user,
                           already_entered=already_entered,
                           is_active=is_active,
                           now=now)


@app.route('/challenges/<challenge_id>/submit', methods=['POST'])
def challenge_submit(challenge_id):
    if 'user' not in session:
        return redirect(url_for('login'))

    challenge = get_challenge_by_id(challenge_id)
    if not challenge:
        flash('Challenge not found.', 'error')
        return redirect(url_for('challenges_list'))

    now = datetime.now()
    if not (challenge['start_date'] <= now <= challenge['end_date']):
        flash('This challenge is no longer accepting entries.', 'error')
        return redirect(url_for('challenge_detail', challenge_id=challenge_id))

    if any(e['author'] == session['user'] for e in challenge['entries']):
        flash('You have already submitted an entry.', 'error')
        return redirect(url_for('challenge_detail', challenge_id=challenge_id))

    image   = request.files.get('image')
    caption = request.form.get('caption', '').strip()

    if not image or not allowed_file(image.filename):
        flash('Please upload a valid image.', 'error')
        return redirect(url_for('challenge_detail', challenge_id=challenge_id))

    ext      = image.filename.rsplit('.', 1)[1].lower()
    filename = f"ch_{uuid.uuid4().hex}.{ext}"
    image.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

    challenge['entries'].append({
        'id':           uuid.uuid4().hex,
        'author':       session['user'],
        'image':        filename,
        'caption':      caption,
        'votes':        [],
        'submitted_at': datetime.now()
    })

    flash('Entry submitted! Good luck.', 'success')
    return redirect(url_for('challenge_detail', challenge_id=challenge_id))


@app.route('/challenges/<challenge_id>/vote/<entry_id>', methods=['POST'])
def challenge_vote(challenge_id, entry_id):
    if 'user' not in session:
        return redirect(url_for('login'))

    challenge = get_challenge_by_id(challenge_id)
    if not challenge:
        return redirect(url_for('challenges_list'))

    entry = next((e for e in challenge['entries'] if e['id'] == entry_id), None)
    if not entry:
        return redirect(url_for('challenge_detail', challenge_id=challenge_id))

    user = session['user']
    if entry['author'] == user:
        flash("You can't vote for your own entry.", 'error')
        return redirect(url_for('challenge_detail', challenge_id=challenge_id))

    # one vote per user per challenge
    already_voted_entry = next(
        (e for e in challenge['entries'] if user in e['votes']), None
    )
    if already_voted_entry:
        already_voted_entry['votes'].remove(user)

    entry['votes'].append(user)
    return redirect(url_for('challenge_detail', challenge_id=challenge_id))


# ─── Run ─────────────────────────────────────────────────────────────────────

if __name__ == '__main__':
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    app.run(debug=True)