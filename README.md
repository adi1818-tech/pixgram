# Pixgram – Instagram Clone 🏔️

A fully functional Instagram-style web app built with Flask.

## Features
- ✅ Register / Login / Logout (session-based auth)
- ✅ Upload photos with captions
- ✅ Like / unlike posts (toggle)
- ✅ Comment on posts
- ✅ Delete your own posts
- ✅ User profile page with post grid
- ✅ Instagram-like UI

---

## Project Structure

```
instagram_clone/
├── app.py                  ← Flask backend (all routes)
├── requirements.txt
├── static/
│   └── uploads/            ← uploaded images saved here (auto-created)
└── templates/
    ├── base.html           ← shared nav + styles
    ├── home.html           ← feed page
    ├── login.html
    ├── register.html
    ├── create.html         ← upload new post
    └── profile.html        ← user profile grid
```

---

## Setup & Run

```bash
# 1. Create & activate virtual environment
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run
python app.py
```

Open **http://127.0.0.1:5000** in your browser.

---

## Next steps (optional upgrades)

| Feature | What to add |
|---|---|
| Persistent storage | Replace `posts = []` / `users = {}` with **SQLite + SQLAlchemy** |
| Follow system | Add `followers` field to users dict / DB table |
| Search | Filter posts by username |
| Stories | Separate model with 24 hr expiry |
| Production deploy | Use **gunicorn** + **Render / Railway / Heroku** |

---

> **Note:** Posts and users are stored in memory and reset when the server restarts.
> For a real app, swap in a database (see upgrade table above).
