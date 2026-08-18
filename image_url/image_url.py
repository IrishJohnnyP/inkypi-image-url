from plugins.base_plugin.base_plugin import BasePlugin
from utils.http_client import get_http_session
from PIL import Image, ImageOps
from io import BytesIO
import logging

logger = logging.getLogger(__name__)

class ImageURL(BasePlugin):
    def generate_image(self, settings, device_config):
        logger.info("=== Image URL Plugin: Starting secure image generation ===")

        url = settings.get('url')
        if not url:
            logger.error("No URL provided in settings")
            raise RuntimeError("URL is required.")

        dimensions = device_config.get_resolution()
        if device_config.get_config("orientation") == "vertical":
            dimensions = dimensions[::-1]
            logger.debug(f"Vertical orientation detected, dimensions: {dimensions[0]}x{dimensions[1]}")

        # --- SECURITY FIX ---
        # Retrieve the key from InkyPi's environment
        app_key = device_config.load_env_key("app_key")
        
        # Safely append the key to the URL
        if app_key:
            separator = "&" if "?" in url else "?"
            secure_url = f"{url}{separator}app_key={app_key}"
        else:
            logger.error("Security Error: app_key was not found by device_config.")
            secure_url = url
        # --------------------

        logger.info("Fetching image securely via HTTP session...")
        logger.debug(f"Target dimensions: {dimensions[0]}x{dimensions[1]}")

        session = get_http_session()
        try:
            # Fetch the raw bytes directly using InkyPi's HTTP session
            response = session.get(secure_url, timeout=40)
            response.raise_for_status()

            # Load into Pillow and ensure RGB format
            image = Image.open(BytesIO(response.content))
            if image.mode != 'RGB':
                image = image.convert('RGB')

            # Perfectly fit and center-crop the image to match screen dimensions
            image = ImageOps.fit(image, dimensions, Image.Resampling.LANCZOS)

        except Exception as e:
            logger.error(f"Failed to load or process image from URL: {e}")
            raise RuntimeError("Failed to load image, please check logs.")

        logger.info("=== Image URL Plugin: Image generation complete ===")
        return image
