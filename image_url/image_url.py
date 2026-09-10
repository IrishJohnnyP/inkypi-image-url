from plugins.base_plugin.base_plugin import BasePlugin
import logging

logger = logging.getLogger(__name__)

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

        # Use BasePlugin's built-in AdaptiveImageLoader instance to ensure 
        # full gamma correction, display profiling, and strict Spectra 6 dithering are applied.
        image = self.image_loader.from_url(secure_url, dimensions, timeout_ms=40000)

        if not image:
            raise RuntimeError("Failed to load image, please check logs.")

        return image
