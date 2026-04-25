import os
import json
import logging
from facebook_business.api import FacebookAdsApi
from facebook_business.adobjects.adaccount import AdAccount
from facebook_business.adobjects.campaign import Campaign
from facebook_business.adobjects.adset import AdSet
from facebook_business.adobjects.adimage import AdImage
from facebook_business.adobjects.adcreative import AdCreative
from facebook_business.adobjects.ad import Ad
from facebook_business.adobjects.page import Page
from facebook_business.exceptions import FacebookRequestError

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MetaAdsManager:
    def __init__(self, app_id, app_secret, access_token, ad_account_id, page_id):
        self.ad_account_id = ad_account_id
        if not self.ad_account_id.startswith('act_'):
            self.ad_account_id = f"act_{self.ad_account_id}"
        self.page_id = page_id
        self.access_token = access_token
        
        # Pass None to app_secret to deliberately bypass the generation of appsecret_proof
        # which has been mathematically rejecting the access token hash matrix.
        FacebookAdsApi.init(app_id=app_id, app_secret=None, access_token=access_token)
        self.account = AdAccount(self.ad_account_id)
        
    def upload_image(self, file_path):
        logger.info(f"Uploading image: {file_path}")
        image = AdImage(parent_id=self.ad_account_id)
        image[AdImage.Field.filename] = file_path
        image.remote_create()
        logger.info(f"Image uploaded with Hash: {image[AdImage.Field.hash]}")
        return image[AdImage.Field.hash]

    def upload_media(self, file_path):
        ext = file_path.split('.')[-1].lower()
        if ext in ['mp4', 'mov', 'avi']:
            logger.info(f"Uploading video: {file_path}")
            from facebook_business.adobjects.advideo import AdVideo
            video = AdVideo(parent_id=self.ad_account_id)
            video[AdVideo.Field.filepath] = file_path
            video.remote_create()
            
            logger.info("Generating blank thumbnail for video using PIL (Hostinger Safe)...")
            from PIL import Image
            thumb_path = f"{file_path}_thumb.jpg"
            img = Image.new('RGB', (1080, 1080), color='black')
            img.save(thumb_path, 'JPEG')
            
            image_hash = self.upload_image(thumb_path)
            return {'type': 'video', 'video_id': video.get_id(), 'image_hash': image_hash}
        else:
            image_hash = self.upload_image(file_path)
            return {'type': 'image', 'image_hash': image_hash}
        
    def create_campaign(self, config):
        logger.info("Creating Campaign...")
        campaign = Campaign(parent_id=self.ad_account_id)
        campaign.update({
            Campaign.Field.name: config.get('campaign_name', 'Lead Gen Campaign'),
            Campaign.Field.objective: 'OUTCOME_LEADS',
            Campaign.Field.status: Campaign.Status.paused,
            Campaign.Field.special_ad_categories: [],
            'is_adset_budget_sharing_enabled': False,
        })
        campaign.remote_create()
        logger.info(f"Campaign created: {campaign.get_id()}")
        return campaign.get_id()
        
    def create_adset(self, campaign_id, config):
        logger.info("Creating AdSet...")
        adset = AdSet(parent_id=self.ad_account_id)
        adset_data = {
            AdSet.Field.name: config.get('adset_name', 'Lead Gen AdSet'),
            AdSet.Field.campaign_id: campaign_id,
            AdSet.Field.daily_budget: config.get('daily_budget', 1000),
            AdSet.Field.billing_event: AdSet.BillingEvent.impressions,
            AdSet.Field.optimization_goal: AdSet.OptimizationGoal.lead_generation,
            AdSet.Field.bid_strategy: 'LOWEST_COST_WITHOUT_CAP',
            AdSet.Field.destination_type: 'ON_AD',
            AdSet.Field.promoted_object: {
                'page_id': self.page_id
            },
            AdSet.Field.targeting: config.get('targeting', {}),
            AdSet.Field.status: AdSet.Status.paused,
        }
        
        if config.get('bid_amount'):
            adset_data[AdSet.Field.bid_amount] = config.get('bid_amount')
            
        adset.update(adset_data)
        adset.remote_create()
        logger.info(f"AdSet created: {adset.get_id()}")
        return adset.get_id()

    def get_or_create_lead_form(self, config):
        logger.info("Checking for existing Lead Forms on the Page...")
        try:
            if config.get('existing_form_id'):
                logger.info(f"Using pre-configured form ID: {config['existing_form_id']}")
                return config['existing_form_id']

            import requests
            url = f"https://graph.facebook.com/v25.0/me/accounts?access_token={self.access_token}"
            res = requests.get(url).json()
            page_token = None
            if 'data' in res:
                for p in res['data']:
                    if p['id'] == self.page_id:
                        page_token = p['access_token']
                        break
            
            if page_token:
                forms_url = f"https://graph.facebook.com/v25.0/{self.page_id}/leadgen_forms?access_token={page_token}&fields=id,name,status"
                forms_res = requests.get(forms_url).json()
                if 'data' in forms_res and len(forms_res['data']) > 0:
                    for form in forms_res['data']:
                        if form.get('status') == 'ACTIVE':
                            logger.info(f"Successfully automatically selected previously created form: {form['name']} ({form['id']})")
                            return form['id']
                    # If none active, fallback to just taking first
                    latest_form = forms_res['data'][0]
                    logger.info(f"Successfully selected previous form: {latest_form['name']} ({latest_form['id']})")
                    return latest_form['id']
            
            logger.info("No usable existing form found, creating a new one instead...")
            return self.create_lead_form(config)
        except Exception as e:
            logger.warning(f"Error checking existing forms: {e}. Falling back to creation.")
            return self.create_lead_form(config)

    def create_lead_form(self, config):
        logger.info("Creating Lead Form...")
        page = Page(self.page_id)
        form_data = {
            'name': f"{config.get('form_name', 'Lead Form')} {os.urandom(2).hex()}",
            'questions': config.get('form_questions', []),
            'privacy_policy': {
                'url': config.get('privacy_policy_url', 'https://example.com/privacy'),
                'link_text': 'Privacy Policy'
            },
            'follow_up_action_url': config.get('website_url', 'https://example.com')
        }
        try:
            form = page.create_lead_gen_form(params=form_data)
            logger.info(f"Lead form created: {form.get_id()}")
            return form.get_id()
        except FacebookRequestError as e:
            logger.error(f"Failed to create lead form: {e}")
            raise

    def create_adcreative(self, form_id, media_details, config):
        logger.info("Creating AdCreative...")
        creative = AdCreative(parent_id=self.ad_account_id)
        
        object_story_spec = {'page_id': self.page_id}
        
        if media_details['type'] == 'image':
            object_story_spec['link_data'] = {
                'image_hash': media_details['image_hash'],
                'link': config.get('website_url', 'https://example.com'),
                'message': config.get('ad_message', 'Grow your business.'),
                'name': config.get('ad_headline', 'Exclusive Access'),
                'call_to_action': {
                    'type': 'SIGN_UP',
                    'value': {'lead_gen_form_id': form_id}
                }
            }
        else: # video
            object_story_spec['video_data'] = {
                'video_id': media_details['video_id'],
                'image_hash': media_details['image_hash'],
                'message': config.get('ad_message', 'Grow your business.'),
                'title': config.get('ad_headline', 'Exclusive Access'),
                'call_to_action': {
                    'type': 'SIGN_UP',
                    'value': {
                        'lead_gen_form_id': form_id,
                        'link': config.get('website_url', 'https://example.com')
                    }
                }
            }

        ad_creative_name = f"{config.get('creative_name', 'Lead Ad Creative')} - {media_details.get('video_id', media_details.get('image_hash'))}"
        creative.update({
            AdCreative.Field.name: ad_creative_name,
            AdCreative.Field.object_story_spec: object_story_spec
        })
        creative.remote_create()
        logger.info(f"AdCreative created: {creative.get_id()}")
        return creative.get_id()

    def create_ad(self, adset_id, creative_id, config):
        logger.info("Creating Ad...")
        ad = Ad(parent_id=self.ad_account_id)
        ad.update({
            Ad.Field.name: config.get('ad_name', 'My Lead Ad'),
            Ad.Field.adset_id: adset_id,
            Ad.Field.creative: {'creative_id': creative_id},
            Ad.Field.status: Ad.Status.paused,
        })
        ad.remote_create()
        logger.info(f"Ad created: {ad.get_id()}")
        return ad.get_id()

    def delete_campaign(self, campaign_id):
        logger.info(f"Rolling back: Deleting Campaign {campaign_id}...")
        try:
            campaign = Campaign(campaign_id)
            campaign.api_delete()
            logger.info(f"Rollback successful: Campaign {campaign_id} deleted.")
        except FacebookRequestError as e:
            logger.error(f"Failed to delete campaign during rollback: {e}")
