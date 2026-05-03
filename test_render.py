from app import app
from flask import render_template
import sqlite3

with app.app_context():
    # Render with is_admin_user=True
    html = render_template('index.html', creds={}, profiles=[], active_profile_id=None, is_admin_user=True)
    if 'Admin Gateway Bubble' in html:
        print("Success: Admin Gateway Bubble is in the HTML")
    else:
        print("Error: Admin Gateway Bubble NOT found in HTML")
