from app import app
from flask import render_template
import sqlite3

with app.app_context():
    # Render with is_admin_user=True
    try:
        html = render_template('index.html', creds={}, profiles=[{'id': 1, 'name': 'Test Profile'}], active_profile_id=1, is_admin_user=True)
        print("Template rendered successfully.")
    except Exception as e:
        print(f"Error rendering template: {e}")
