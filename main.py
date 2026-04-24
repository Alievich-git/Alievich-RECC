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
        # Step A: Image Upload
        image_hash = manager.upload_image(config.get('ad_image_path', 'ad_image.png'))
        
        # Step B: Campaign
        campaign_id = manager.create_campaign(config)
        
        try:
            # Step C: AdSet
            adset_id = manager.create_adset(campaign_id, config)
            
            # Step D: Lead Form
            form_id = manager.get_or_create_lead_form(config)
            
            # Step E: AdCreative
            creative_id = manager.create_adcreative(form_id, image_hash, config)
            
            # Step F: Ad
            ad_id = manager.create_ad(adset_id, creative_id, config)
            
            logger.info("\n========== SUCCESS ==========")
            logger.info("Your Campaign is officially built and PAUSED in Ads Manager.")
            logger.info(f"Campaign ID: {campaign_id}")
            logger.info(f"AdSet ID: {adset_id}")
            logger.info(f"Lead Form ID: {form_id}")
            logger.info(f"Ad ID: {ad_id}")
            logger.info("=============================")
            
        except Exception as e:
            logger.error(f"Process failed during component creation: {e}")
            manager.delete_campaign(campaign_id)
            raise e

    except Exception as e:
        logger.error(f"Process totally failed: {e}")

if __name__ == "__main__":
    main()
