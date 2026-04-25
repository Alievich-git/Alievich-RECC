import os
import json
import logging
import sqlite3
from flask import Flask, request, jsonify, render_template, session, redirect, url_for
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from meta_ads_api import MetaAdsManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
# Cryptographically secure session key for Hostinger production deployment
app.secret_key = os.environ.get("FLASK_SECRET_KEY", os.urandom(32).hex())
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 1000 * 1024 * 1024 # 1GB max per request

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# --- Database Initialization ---
def init_db():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE, password_hash TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS profiles
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, name TEXT, meta_app_id TEXT, 
                  meta_app_secret TEXT, access_token TEXT, ad_account_id TEXT, page_id TEXT,
                  FOREIGN KEY(user_id) REFERENCES users(id))''')
    conn.commit()
    conn.close()

init_db()

def get_db():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

# --- Authentication Wall ---
@app.before_request
def require_login():
    allowed_routes = ['login', 'register', 'static']
    if request.endpoint not in allowed_routes and 'user_id' not in session:
        return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
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
    return redirect(url_for('index'))

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('active_profile_id', None)
    return redirect(url_for('login'))

@app.route('/')
def index():
    db = get_db()
    profiles = db.execute('SELECT id, name FROM profiles WHERE user_id = ?', (session['user_id'],)).fetchall()
    
    active_id = session.get('active_profile_id')
    if not active_id and profiles:
        active_id = profiles[0]['id']
        session['active_profile_id'] = active_id
        
    creds = None
    if active_id:
        creds = db.execute('SELECT * FROM profiles WHERE id = ? AND user_id = ?', (active_id, session['user_id'])).fetchone()
        
    db.close()
    return render_template('index.html', creds=creds or {}, profiles=profiles, active_profile_id=active_id)

@app.route('/api/create_profile', methods=['POST'])
def create_profile():
    name = request.form.get('name', '').strip()
    if not name:
        return jsonify({'success': False, 'message': 'Name is required'})
    db = get_db()
    db.execute('INSERT INTO profiles (user_id, name) VALUES (?, ?)', (session['user_id'], name))
    db.commit()
    new_profile = db.execute('SELECT id FROM profiles WHERE user_id = ? AND name = ? ORDER BY id DESC LIMIT 1', (session['user_id'], name)).fetchone()
    db.close()
    session['active_profile_id'] = new_profile['id']
    return jsonify({'success': True})

@app.route('/api/switch_profile', methods=['POST'])
def switch_profile():
    profile_id = request.form.get('profile_id')
    if profile_id:
        session['active_profile_id'] = int(profile_id)
    return jsonify({'success': True})

@app.route('/api/save_credentials', methods=['POST'])
def save_credentials():
    profile_id = session.get('active_profile_id')
    if not profile_id:
        return jsonify({'success': False, 'message': 'No profile active'}), 400
        
    data = request.form
    app_id = data.get('app_id', '').strip()
    app_secret = data.get('app_secret', '').strip()
    access_token = data.get('access_token', '').strip()
    ad_account_id = data.get('ad_account_id', '').strip()
    page_id = data.get('page_id', '').strip()
    
    db = get_db()
    db.execute('''UPDATE profiles SET 
                  meta_app_id=?, meta_app_secret=?, access_token=?, ad_account_id=?, page_id=? 
                  WHERE id=? AND user_id=?''', 
               (app_id, app_secret, access_token, ad_account_id, page_id, profile_id, session['user_id']))
    db.commit()
    db.close()
    
    return jsonify({'success': True})

@app.route('/api/deploy_campaign', methods=['POST'])
def deploy_campaign():
    try:
        data = request.form
        
        # 1. Extract Credentials dynamically
        app_id = data.get('app_id', '').strip()
        app_secret = data.get('app_secret', '').strip()
        access_token = data.get('access_token', '').strip()
        ad_account_id = data.get('ad_account_id', '').strip()
        page_id = data.get('page_id', '').strip()
        
        if not all([app_id, app_secret, access_token, ad_account_id, page_id]):
            return jsonify({'success': False, 'message': 'Missing Meta credentials'}), 400

        # Auto-Save Credentials for the active profile
        profile_id = session.get('active_profile_id')
        if profile_id:
            db = get_db()
            db.execute('''UPDATE profiles SET 
                          meta_app_id=?, meta_app_secret=?, access_token=?, ad_account_id=?, page_id=? 
                          WHERE id=? AND user_id=?''', 
                       (app_id, app_secret, access_token, ad_account_id, page_id, profile_id, session['user_id']))
            db.commit()
            db.close()

        # Load master config structure
        try:
            with open('config.json', 'r') as f:
                config = json.load(f)
        except Exception as e:
            return jsonify({'success': False, 'message': 'Engine error: missing internal config.json'}), 500

        # Override user inputs
        config['campaign_name'] = "Ali Alievich | RECC"
        
        primary_text = data.get('primary_text')
        if primary_text:
            config['ad_message'] = primary_text
            
        daily_budget = data.get('daily_budget')
        if daily_budget:
            # Meta requires the budget in the lowest denomination (e.g., cents/piasters). 
            # If the user inputs 350 (meaning 350 EGP), we must multiply by 100 internally -> 35000
            config['daily_budget'] = int(float(daily_budget) * 100)

        # 2. Handle Files
        files = request.files.getlist('files[]')
        media_files = []
        if not files or files[0].filename == '':
            return jsonify({'success': False, 'message': 'No media files uploaded'}), 400
            
        for file in files:
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            
            # Universal Force-Normalization for Meta Ads
            ext = filename.split('.')[-1].lower()
            if ext not in ['mp4', 'mov', 'avi']: # If it's not a video, force it to be a clean JPEG
                try:
                    from PIL import Image
                    img = Image.open(file_path)
                    new_path = file_path + '.jpg'
                    if img.mode in ("RGBA", "P"): 
                        img = img.convert("RGB")
                    # Force 100% quality and disable chroma subsampling to prevent heavy pixelation on Meta Ads
                    img.save(new_path, 'JPEG', quality=100, subsampling=0)
                    os.remove(file_path)
                    file_path = new_path
                    logger.info(f"Force-normalized image to JPEG: {new_path}")
                except Exception as e:
                    logger.warning(f"Could not normalize image {filename}: {e}")
                    
            media_files.append(file_path)
            
        config['media_files'] = media_files

        # 3. Initialize the Manager with dynamic credentials
        manager = MetaAdsManager(app_id, app_secret, access_token, ad_account_id, page_id)
        
        # Step B: Campaign
        campaign_id = manager.create_campaign(config)
        
        try:
            # Step D: Lead Form
            form_id = manager.get_or_create_lead_form(config)
            
            adset_ids = []
            ad_ids = []

            for index, file_path in enumerate(media_files):
                logger.info(f"--- Processing Creative {index + 1}/{len(media_files)}: {file_path} ---")
                
                media_details = manager.upload_media(file_path)
                
                # Clone adset structure logically isolating the creative
                current_config = config.copy()
                basename = os.path.basename(file_path)
                current_config['adset_name'] = f"{config.get('adset_name', 'Lead Gen AdSet')} - {basename}"
                current_config['creative_name'] = f"{config.get('creative_name', 'Lead Ad Creative')} - {basename}"
                current_config['ad_name'] = f"{config.get('ad_name', 'My Lead Ad')} - {basename}"

                adset_id = manager.create_adset(campaign_id, current_config)
                adset_ids.append(adset_id)
                
                creative_id = manager.create_adcreative(form_id, media_details, current_config)
                
                ad_id = manager.create_ad(adset_id, creative_id, current_config)
                ad_ids.append(ad_id)
            
            # Clean up uploaded files after processing
            for file_path in media_files:
                if os.path.exists(file_path):
                    os.remove(file_path)
                thumb = file_path + "_thumb.jpg"
                if os.path.exists(thumb):
                    os.remove(thumb)

            return jsonify({
                'success': True,
                'data': {
                    'campaign_id': campaign_id,
                    'form_id': form_id,
                    'adsets_created': len(adset_ids),
                    'ad_ids': ad_ids
                }
            })

        except Exception as e:
            logger.error(f"Generation failed: {e}")
            manager.delete_campaign(campaign_id)
            return jsonify({'success': False, 'message': f"API Error: {str(e)}"}), 500

    except Exception as e:
        logger.error(f"Global server error: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3102, debug=True)
