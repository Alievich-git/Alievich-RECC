import re

with open('meta_ads_api.py', 'r') as f:
    api = f.read()

# Replace cv2 logic with PIL blank thumbnail
cv2_block = """
            logger.info("Extracting thumbnail for video using OpenCV...")
            import cv2
            cap = cv2.VideoCapture(file_path)
            ret, frame = cap.read()
            cap.release()
            
            thumb_path = f"{file_path}_thumb.jpg"
            if ret:
                cv2.imwrite(thumb_path, frame)
            else:
                logger.error("Failed to extract thumbnail from video.")
"""

pil_block = """
            logger.info("Generating blank thumbnail for video using PIL (Hostinger Safe)...")
            from PIL import Image
            thumb_path = f"{file_path}_thumb.jpg"
            img = Image.new('RGB', (1080, 1080), color='black')
            img.save(thumb_path, 'JPEG')
"""

api = api.replace(cv2_block.strip(), pil_block.strip())

with open('meta_ads_api.py', 'w') as f:
    f.write(api)

with open('static/script.js', 'r') as f:
    js = f.read()

js = js.replace(
    'result = { success: false, message: "Invalid JSON response from server." };',
    'result = { success: false, message: "Server Crash/HTML Returned\\n\\n" + xhr.responseText.substring(0, 500) };'
)

with open('static/script.js', 'w') as f:
    f.write(js)
