import os
with open('app.py', 'r') as f:
    content = f.read()

# 1. init_db
old_init_db_end = """    c.execute('''CREATE TABLE IF NOT EXISTS profiles
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, name TEXT, meta_app_id TEXT, 
                  meta_app_secret TEXT, access_token TEXT, ad_account_id TEXT, page_id TEXT,
                  FOREIGN KEY(user_id) REFERENCES users(id))''')
    conn.commit()
    conn.close()"""

new_init_db_end = """    c.execute('''CREATE TABLE IF NOT EXISTS profiles
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, name TEXT, meta_app_id TEXT, 
                  meta_app_secret TEXT, access_token TEXT, ad_account_id TEXT, page_id TEXT,
                  FOREIGN KEY(user_id) REFERENCES users(id))''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS invite_codes
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, code TEXT UNIQUE, is_used BOOLEAN DEFAULT 0, used_by INTEGER,
                  FOREIGN KEY(used_by) REFERENCES users(id))''')
    conn.commit()
    conn.close()"""
content = content.replace(old_init_db_end, new_init_db_end)

# 3. Update /register
old_register = """@app.route('/register', methods=['POST'])
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

new_register = """@app.route('/register', methods=['POST'])
def register():
    email = request.form.get('email', '').strip()
    password = request.form.get('password', '')
    invite_code = request.form.get('invite_code', '').strip()
    
    if not email or not password or not invite_code:
        return render_template('login.html', error="Email, password, and invite code are required.")
        
    db = get_db()
    # Validate Invite Code
    code_record = db.execute('SELECT * FROM invite_codes WHERE code = ? AND is_used = 0', (invite_code,)).fetchone()
    if not code_record:
        db.close()
        return render_template('login.html', error="Invalid or already used invite code.")
        
    existing = db.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()
    if existing:
        db.close()
        return render_template('login.html', error="Email already taken.")
        
    db.execute('INSERT INTO users (email, password_hash) VALUES (?, ?)', 
               (email, generate_password_hash(password, method='pbkdf2:sha256')))
    db.commit()
    user = db.execute('SELECT id FROM users WHERE email = ?', (email,)).fetchone()
    
    # Mark invite code as used
    db.execute('UPDATE invite_codes SET is_used = 1, used_by = ? WHERE id = ?', (user['id'], code_record['id']))
    
    db.execute('INSERT INTO profiles (user_id, name) VALUES (?, ?)', (user['id'], 'Main Profile'))
    db.commit()
    profile = db.execute('SELECT id FROM profiles WHERE user_id = ? AND name = ?', (user['id'], 'Main Profile')).fetchone()
    db.close()
    
    session.permanent = True
    session['user_id'] = user['id']
    session['active_profile_id'] = profile['id']
    return redirect(url_for('index'))"""
content = content.replace(old_register, new_register)

# 4. Add Admin route
admin_routes = """
import string
import random
import os

def is_admin(email):
    # Retrieve from .env or default to the owner's email
    admin_email = os.environ.get('ADMIN_EMAIL', 'aliali.elsheikh1@gmail.com')
    return email.lower() == admin_email.lower()

@app.route('/admin/invites', methods=['GET', 'POST'])
def admin_invites():
    if 'user_id' not in session:
        return redirect(url_for('login'))
        
    db = get_db()
    user = db.execute('SELECT * FROM users WHERE id = ?', (session['user_id'],)).fetchone()
    
    if not user or not is_admin(user['email']):
        db.close()
        return "Access Denied. You are not an administrator.", 403
        
    if request.method == 'POST':
        # Generate new code: RECC-XXXX-XXXX
        parts = [''.join(random.choices(string.ascii_uppercase + string.digits, k=4)) for _ in range(2)]
        new_code = f"RECC-{parts[0]}-{parts[1]}"
        db.execute('INSERT INTO invite_codes (code) VALUES (?)', (new_code,))
        db.commit()
        
    # Fetch all codes
    codes = db.execute('''SELECT invite_codes.*, users.email as used_by_email 
                          FROM invite_codes 
                          LEFT JOIN users ON invite_codes.used_by = users.id 
                          ORDER BY invite_codes.id DESC''').fetchall()
    db.close()
    
    return render_template('admin_invites.html', codes=codes)
"""

content = content.replace("@app.route('/logout')", admin_routes + "\n@app.route('/logout')")

with open('app.py', 'w') as f:
    f.write(content)
