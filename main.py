import os
import json
import logging
from dotenv import load_dotenv
from meta_ads_api import MetaAdsManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    # 1. Load environment variables
    load_dotenv()
    
    app_id = os.getenv('META_APP_ID')
    app_secret = os.getenv('META_APP_SECRET')
    access_token = os.getenv('META_ACCESS_TOKEN')
    ad_account_id = os.getenv('META_AD_ACCOUNT_ID')
    page_id = os.getenv('META_PAGE_ID')

    if not all([app_id, app_secret, access_token, ad_account_id, page_id]):
        logger.error("Missing one or more META credentials in .env file.")
        return

    # 2. Load configuration
    try:
        with open('config.json', 'r') as f:
            config = json.load(f)
    except FileNotFoundError:
        logger.error("config.json not found.")
        return

    # 3. Initialize the Manager
    manager = MetaAdsManager(app_id, app_secret, access_token, ad_account_id, page_id)
    
    # 4. Execute the sequence
    try:
        # Step B: Campaign
        campaign_id = manager.create_campaign(config)
        
        try:
            # Step D: Lead Form (Outside loop to share the exact same form)
            form_id = manager.get_or_create_lead_form(config)
            
            media_files = config.get('media_files', [])
            if not media_files:
                logger.error("No media_files found in config.json")
                return
            
            adset_ids = []
            ad_ids = []

            for index, file_path in enumerate(media_files):
                logger.info(f"--- Processing Creative {index + 1}/{len(media_files)}: {file_path} ---")
                
                # Upload matching media type using the unified processor
                media_details = manager.upload_media(file_path)
                
                # Clone adset structure logically isolating the creative
                current_config = config.copy()
                current_config['adset_name'] = f"{config.get('adset_name', 'Lead Gen AdSet')} - {file_path}"
                current_config['creative_name'] = f"{config.get('creative_name', 'Lead Ad Creative')} - {file_path}"
                current_config['ad_name'] = f"{config.get('ad_name', 'My Lead Ad')} - {file_path}"

                # Step C: AdSet
                adset_id = manager.create_adset(campaign_id, current_config)
                adset_ids.append(adset_id)
                
                # Step E: AdCreative
                creative_id = manager.create_adcreative(form_id, media_details, current_config)
                
                # Step F: Ad
                ad_id = manager.create_ad(adset_id, creative_id, current_config)
                ad_ids.append(ad_id)
            
            logger.info("\n========== SUCCESS ==========")
            logger.info("Your Campaign is officially built and PAUSED in Ads Manager.")
            logger.info(f"Campaign ID: {campaign_id}")
            logger.info(f"Lead Form ID: {form_id}")
            logger.info(f"Generated {len(adset_ids)} AdSets and Ads.")
            logger.info("=============================")
            
        except Exception as e:
            logger.error(f"Process failed during component creation: {e}")
            manager.delete_campaign(campaign_id)
            raise e

    except Exception as e:
        logger.error(f"Process totally failed: {e}")

if __name__ == "__main__":
    main()
