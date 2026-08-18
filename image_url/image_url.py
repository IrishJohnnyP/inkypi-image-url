from plugins.base_plugin.base_plugin import BasePlugin
import logging

logger = logging.getLogger(__name__)

class ImageURL(BasePlugin):
    
    def _get_auth_headers(self, app_key):
        """Builds the custom headers needed to pass the Cloudflare Worker security check."""
        if not app_key:
            logger.error("Security Error: app_key was not found by device_config.")
            return {}
        return {"X-App-Key": app_key}

    def generate_image(self, settings, device_config):
        logger.info("=== Image URL Plugin: Starting image generation ===")

        url = settings.get('url')
        if not url:
            logger.error("No URL provided in settings")
            raise RuntimeError("URL is required.")

        dimensions = device_config.get_resolution()
        if device_config.get_config("orientation") == "vertical":
            dimensions = dimensions[::-1]
            logger.debug(f"Vertical orientation detected, dimensions: {dimensions[0]}x{dimensions[1]}")

        logger.info(f"Fetching image from URL: {url}")
        logger.debug(f"Target dimensions: {dimensions[0]}x{dimensions[1]}")

        # --- SECURITY FIX ---
        # Retrieve the key from InkyPi's environment
        app_key = device_config.load_env_key("app_key")
        auth_headers = self._get_auth_headers(app_key)
        # --------------------

        # Use adaptive image loader for memory-efficient processing
        # We pass the auth_headers down into the loader so it can authenticate with the Worker
        image = self.image_loader.from_url(url, dimensions, timeout_ms=40000, headers=auth_headers)

        if not image:
            logger.error("Failed to load image from URL")
            raise RuntimeError("Failed to load image, please check logs.")

        logger.info("=== Image URL Plugin: Image generation complete ===")
        return image
