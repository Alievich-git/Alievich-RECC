import os
import json
import logging
from flask import Flask, request, jsonify, render_template
from werkzeug.utils import secure_filename
from meta_ads_api import MetaAdsManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 1000 * 1024 * 1024 # 1GB max per request

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

@app.route('/')
def index():
    return render_template('index.html')

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
                    img.save(new_path, 'JPEG', quality=95)
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
