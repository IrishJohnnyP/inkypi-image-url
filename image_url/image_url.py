from plugins.base_plugin.base_plugin import BasePlugin
from PIL import Image
from io import BytesIO
import requests
import logging

logger = logging.getLogger(__name__)

def grab_image(image_url, dimensions, timeout_ms=40000):
    """Grab an image from a URL and resize it to the specified dimensions."""
    try:
        response = requests.get(image_url, timeout=timeout_ms / 1000)
        response.raise_for_status()
        img = Image.open(BytesIO(response.content))
        img = img.convert("RGB")
        img = img.resize(dimensions, Image.LANCZOS)
        return img
    except Exception as e:
        logger.error(f"Error grabbing image from {image_url}: {e}")
        return None

class ImageURL(BasePlugin):
    def generate_image(self, settings, device_config):
        url = settings.get('url')
        if not url:
            raise RuntimeError("URL is required.")

        dimensions = device_config.get_resolution()
        if device_config.get_config("orientation") == "vertical":
            dimensions = dimensions[::-1]

        # --- SECURITY FIX ---
        # Retrieve the key from InkyPi's environment and append securely to the URL
        app_key = device_config.load_env_key("app_key")
        if app_key:
            separator = "&" if "?" in url else "?"
            secure_url = f"{url}{separator}app_key={app_key}"
        else:
            logger.error("Security Error: app_key was not found by device_config.")
            secure_url = url
        # --------------------

        logger.info(f"Grabbing image securely from: {url}")

        image = grab_image(secure_url, dimensions, timeout_ms=40000)

        if not image:
            raise RuntimeError("Failed to load image, please check logs.")

        return image
