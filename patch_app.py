import sys

with open('app.py', 'r') as f:
    content = f.read()

# Add imports
imports_add = """from flask import Flask, request, jsonify, render_template, session, redirect, url_for
from datetime import timedelta
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import time
import secrets
from dotenv import load_dotenv

load_dotenv()
"""
content = content.replace("from flask import Flask, request, jsonify, render_template, session, redirect, url_for", imports_add)

# Configure permanent session lifetime
config_add = """app.config['MAX_CONTENT_LENGTH'] = 1000 * 1024 * 1024 # 1GB max per request
app.permanent_session_lifetime = timedelta(days=30)
"""
content = content.replace("app.config['MAX_CONTENT_LENGTH'] = 1000 * 1024 * 1024 # 1GB max per request", config_add)

# Update init_db
old_init_db = """def init_db():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE, password_hash TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS profiles
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, name TEXT, meta_app_id TEXT, 
                  meta_app_secret TEXT, access_token TEXT, ad_account_id TEXT, page_id TEXT,
                  FOREIGN KEY(user_id) REFERENCES users(id))''')
    conn.commit()
    conn.close()"""

new_init_db = """def init_db():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, email TEXT UNIQUE, password_hash TEXT)''')
    
    try:
        c.execute("ALTER TABLE users RENAME COLUMN username TO email")
    except Exception:
        pass
        
    try:
        c.execute("ALTER TABLE users ADD COLUMN reset_token TEXT")
        c.execute("ALTER TABLE users ADD COLUMN reset_token_expiry REAL")
    except Exception:
        pass

    c.execute('''CREATE TABLE IF NOT EXISTS profiles
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, name TEXT, meta_app_id TEXT, 
                  meta_app_secret TEXT, access_token TEXT, ad_account_id TEXT, page_id TEXT,
                  FOREIGN KEY(user_id) REFERENCES users(id))''')
    conn.commit()
    conn.close()"""
content = content.replace(old_init_db, new_init_db)

# Replace login and register
old_login_reg = """@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password']
        db = get_db()
        user = db.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
        db.close()
        
        if user and check_password_hash(user['password_hash'], password):
            session['user_id'] = user['id']
            db = get_db()
            profile = db.execute('SELECT id FROM profiles WHERE user_id = ? LIMIT 1', (user['id'],)).fetchone()
            db.close()
            session['active_profile_id'] = profile['id'] if profile else None
            return redirect(url_for('index'))
        else:
            return render_template('login.html', error="Invalid username or password.")
    return render_template('login.html')

@app.route('/register', methods=['POST'])
def register():
    username = request.form['username'].strip()
    password = request.form['password']
    if not username or not password:
        return render_template('login.html', error="Username and password required.")
        
    db = get_db()
    existing = db.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
    if existing:
        db.close()
        return render_template('login.html', error="Username already taken.")
        
    db.execute('INSERT INTO users (username, password_hash) VALUES (?, ?)', 
               (username, generate_password_hash(password, method='pbkdf2:sha256')))
    db.commit()
    user = db.execute('SELECT id FROM users WHERE username = ?', (username,)).fetchone()
    db.execute('INSERT INTO profiles (user_id, name) VALUES (?, ?)', (user['id'], 'Main Profile'))
    db.commit()
    profile = db.execute('SELECT id FROM profiles WHERE user_id = ? AND name = ?', (user['id'], 'Main Profile')).fetchone()
    db.close()
    
    session['user_id'] = user['id']
    session['active_profile_id'] = profile['id']
    return redirect(url_for('index'))"""

new_login_reg = """@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        remember = 'remember' in request.form
        db = get_db()
        user = db.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()
        db.close()
        
        if user and check_password_hash(user['password_hash'], password):
            session.permanent = remember
            session['user_id'] = user['id']
            db = get_db()
            profile = db.execute('SELECT id FROM profiles WHERE user_id = ? LIMIT 1', (user['id'],)).fetchone()
            db.close()
            session['active_profile_id'] = profile['id'] if profile else None
            return redirect(url_for('index'))
        else:
            return render_template('login.html', error="Invalid email or password.")
    return render_template('login.html')

@app.route('/register', methods=['POST'])
def register():
    email = request.form.get('email', '').strip()
    password = request.form.get('password', '')
    if not email or not password:
        return render_template('login.html', error="Email and password required.")
        
    db = get_db()
    existing = db.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()
    if existing:
        db.close()
        return render_template('login.html', error="Email already taken.")
        
    db.execute('INSERT INTO users (email, password_hash) VALUES (?, ?)', 
               (email, generate_password_hash(password, method='pbkdf2:sha256')))
    db.commit()
    user = db.execute('SELECT id FROM users WHERE email = ?', (email,)).fetchone()
    db.execute('INSERT INTO profiles (user_id, name) VALUES (?, ?)', (user['id'], 'Main Profile'))
    db.commit()
    profile = db.execute('SELECT id FROM profiles WHERE user_id = ? AND name = ?', (user['id'], 'Main Profile')).fetchone()
    db.close()
    
    session.permanent = True
    session['user_id'] = user['id']
    session['active_profile_id'] = profile['id']
    return redirect(url_for('index'))"""
content = content.replace(old_login_reg, new_login_reg)

forgot_password_routes = """
@app.route('/forgot_password', methods=['POST'])
def forgot_password():
    data = request.json
    email = data.get('email', '').strip()
    if not email:
        return jsonify({'success': False, 'message': 'Email required.'})
    
    db = get_db()
    user = db.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()
    if not user:
        db.close()
        return jsonify({'success': True}) # Prevent email enumeration
        
    token = secrets.token_urlsafe(32)
    expiry = time.time() + 900 # 15 minutes
    db.execute('UPDATE users SET reset_token = ?, reset_token_expiry = ? WHERE id = ?', (token, expiry, user['id']))
    db.commit()
    db.close()
    
    # Send Email
    try:
        smtp_user = os.environ.get('SMTP_USER', 'hello@roienv.com')
        smtp_pass = os.environ.get('SMTP_PASS')
        if not smtp_pass:
            logger.error("SMTP_PASS not found in environment.")
            return jsonify({'success': False, 'message': 'Email sending disabled internally.'})
            
        msg = MIMEMultipart()
        msg['From'] = smtp_user
        msg['To'] = email
        msg['Subject'] = 'RECC - Password Reset Request'
        
        reset_link = f"{request.host_url.rstrip('/')}/reset_password/{token}"
        body = f"Hello,\\n\\nPlease click the link below to reset your password. This link expires in 15 minutes.\\n\\n{reset_link}\\n\\nIf you did not request this, please ignore this email."
        msg.attach(MIMEText(body, 'plain'))
        
        server = smtplib.SMTP('smtp.hostinger.com', 587)
        server.starttls()
        server.login(smtp_user, smtp_pass)
        server.send_message(msg)
        server.quit()
        return jsonify({'success': True})
    except Exception as e:
        logger.error(f"Failed to send email: {e}")
        return jsonify({'success': False, 'message': 'Failed to dispatch email. Please try again later.'})

@app.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    db = get_db()
    user = db.execute('SELECT * FROM users WHERE reset_token = ?', (token,)).fetchone()
    if not user or time.time() > (user['reset_token_expiry'] or 0):
        db.close()
        return render_template('reset_password.html', error="Invalid or expired reset token.")
        
    if request.method == 'POST':
        new_password = request.form['password']
        if len(new_password) < 6:
            return render_template('reset_password.html', error="Password too short.")
        
        hashed = generate_password_hash(new_password, method='pbkdf2:sha256')
        db.execute('UPDATE users SET password_hash = ?, reset_token = NULL, reset_token_expiry = NULL WHERE id = ?', (hashed, user['id']))
        db.commit()
        db.close()
        return render_template('reset_password.html', success="Password successfully updated! You may now close this page and log in.")
        
    db.close()
    return render_template('reset_password.html', token=token)

"""

content = content.replace("@app.route('/logout')", forgot_password_routes + "\n@app.route('/logout')")

with open('app.py', 'w') as f:
    f.write(content)

