from plugins.base_plugin.base_plugin import BasePlugin
import logging
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logger = logging.getLogger(__name__)

# OPTIONAL: Silence the underlying urllib3 retry warnings globally 
# since we know the Cloudflare proxy naturally causes them.
logging.getLogger("urllib3.connectionpool").setLevel(logging.ERROR)

class ImageURL(BasePlugin):
    def generate_image(self, settings, device_config):
        url = settings.get('url')
        if not url:
            raise RuntimeError("URL is required.")

        dimensions = device_config.get_resolution()
        if device_config.get_config("orientation") == "vertical":
            dimensions = dimensions[::-1]

        # --- SECURITY FIX ---
        app_key = device_config.load_env_key("app_key")
        if app_key:
            separator = "&" if "?" in url else "?"
            secure_url = f"{url}{separator}app_key={app_key}"
        else:
            logger.error("Security Error: app_key was not found by device_config.")
            secure_url = url
        # --------------------

        # FIX 1: Log the actual secure_url so you know the key is attached
        logger.info(f"Grabbing image securely from: {secure_url}")

        # FIX 2: Pre-warm the Cloudflare worker to prevent urllib3 timeouts
        self._pre_warm_worker(secure_url)

        # Use BasePlugin's built-in AdaptiveImageLoader instance.
        # Now that the worker is awake, this will likely succeed on the first try.
        image = self.image_loader.from_url(secure_url, dimensions, timeout_ms=40000)

        if not image:
            raise RuntimeError("Failed to load image, please check logs.")

        return image

    def _pre_warm_worker(self, target_url):
        """
        Wakes up the Cloudflare Worker using a dedicated session.
        This absorbs the initial connection drop gracefully without spamming logs.
        """
        session = requests.Session()
        
        # Configure explicit retries and a backoff timer for this warmup
        retries = Retry(total=3, backoff_factor=0.5, status_forcelist=[500, 502, 503, 504])
        session.mount('https://', HTTPAdapter(max_retries=retries))
        
        try:
            # We use stream=True so we don't download the actual image bytes twice.
            # We just want to establish the connection and get the HTTP headers.
            with session.get(target_url, timeout=(5.0, 10.0), stream=True) as response:
                response.raise_for_status()
        except Exception as e:
            # We log this as debug so it doesn't clutter the main INFO log.
            # Even if the pre-warm drops, we still let image_loader try anyway.
            logger.debug(f"Pre-warm request dropped, but worker should be awake: {e}")
