const BASE62_ALPHABET = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz";

function getPartition(token) {
  if (!token || token.length < 2) return "23";
  const raw = token.startsWith("A") ? token.substring(1, 2) : token.substring(1, 3);
  let decoded = 0;
  for (let i = 0; i < raw.length; i++) {
    const idx = BASE62_ALPHABET.indexOf(raw[i]);
    if (idx === -1) return "23";
    decoded = decoded * 62 + idx;
  }
  return decoded;
}

function getLargestDerivativeChecksum(derivatives) {
  if (!derivatives || typeof derivatives !== "object") return null;
  let maxArea = -1;
  let bestChecksum = null;

  for (const derivative of Object.values(derivatives)) {
    if (!derivative || typeof derivative !== "object" || !derivative.checksum) continue;
    const width = parseInt(derivative.width, 10) || 0;
    const height = parseInt(derivative.height, 10) || 0;
    const area = width * height;
    if (area > maxArea) {
      maxArea = area;
      bestChecksum = derivative.checksum;
    }
  }
  return bestChecksum;
}

async function safeFetchJson(url, options) {
  for (let i = 0; i < 3; i++) {
    try {
      const res = await fetch(url, options);
      const text = await res.text();
      if (!text) continue;
      return JSON.parse(text);
    } catch {
      continue;
    }
  }
  return null;
}

export default {
  async fetch(request, env) {
    // --- SECURITY CHECK ---
    const url = new URL(request.url);
    // Look for the key in either the Headers OR the URL query parameters
    const clientKey = request.headers.get('X-App-Key') || url.searchParams.get('app_key');
    
    if (!clientKey || clientKey !== env.app_key) {
      return new Response("Unauthorized", { status: 401 });
    }
    // ----------------------

    try {
      if (!env.KV) {
        return new Response("KV binding missing (name must be KV)", { status: 500 });
      }

      const albumKey = url.searchParams.get("album");

      if (!albumKey) {
        return new Response("Missing album (?album=album1)", { status: 400 });
      }

      let token = env[albumKey];
      if (!token) {
        return new Response(`Invalid album key: ${albumKey}`, { status: 400 });
      }

      if (token.startsWith("#")) {
        token = token.substring(1);
      }

      const stateKey = `album:${albumKey}:state`;
      const cacheKey = `album:${albumKey}:metadataCache`;

      const partition = getPartition(token);
      let baseApi = `https://p${partition}-sharedstreams.icloud.com/${token}/sharedstreams`;

      let streamJson = await safeFetchJson(`${baseApi}/webstream`, {
        method: "POST",
        headers: { "Content-Type": "text/plain" },
        body: JSON.stringify({ streamCtag: null })
      });

      let cache = await env.KV.get(cacheKey, { type: "json" });

      if (streamJson) {
        const redirectHost = streamJson?.["X-Apple-MMe-Host"];
        if (redirectHost) {
          baseApi = `https://${redirectHost}/${token}/sharedstreams`;
          const retry = await safeFetchJson(`${baseApi}/webstream`, {
            method: "POST",
            headers: { "Content-Type": "text/plain" },
            body: JSON.stringify({ streamCtag: null })
          });
          if (retry) streamJson = retry;
        }

        const photos = streamJson?.photos;

        if (Array.isArray(photos) && photos.length > 0) {
          const photoMap = {};

          for (const photo of photos) {
            if (!photo?.photoGuid || !photo?.derivatives) continue;
            const checksum = getLargestDerivativeChecksum(photo.derivatives);
            if (checksum) {
              photoMap[photo.photoGuid] = checksum;
            }
          }

          const currentGuids = Object.keys(photoMap);
          const cacheValid =
            cache &&
            Array.isArray(cache.ids) &&
            cache.ids.length === currentGuids.length &&
            cache.ids.every(id => currentGuids.includes(id));

          if (!cacheValid && currentGuids.length > 0) {
            cache = { ids: currentGuids, map: photoMap };
            await env.KV.put(cacheKey, JSON.stringify(cache), {
              expirationTtl: 86400
            });
          }
        }
      }

      if (!cache || !cache.ids?.length) {
        return new Response("Apple API unavailable and no metadata cached yet", { status: 502 });
      }

      // --- STATE MANAGEMENT ---
      let state = await env.KV.get(stateKey, { type: "json" });
      if (!state || !Array.isArray(state.remaining)) {
        state = { remaining: [] };
      }

      const shuffleDeck = (ids) => {
        let deck = [...ids];
        for (let i = deck.length - 1; i > 0; i--) {
          const j = Math.floor(Math.random() * (i + 1));
          [deck[i], deck[j]] = [deck[j], deck[i]];
        }
        return deck;
      };

      if (state.remaining.length === 0) {
        state.remaining = shuffleDeck(cache.ids);
      } else {
        state.remaining = state.remaining.filter(id => cache.ids.includes(id));
        if (state.remaining.length === 0) {
          state.remaining = shuffleDeck(cache.ids);
        }
      }

      const selectedId = state.remaining.pop();
      const selectedChecksum = cache.map[selectedId];

      await env.KV.put(stateKey, JSON.stringify(state), {
        expirationTtl: 604800
      });

      // --- FETCH FRESH URL ---
      const assetJson = await safeFetchJson(`${baseApi}/webasseturls`, {
        method: "POST",
        headers: { "Content-Type": "text/plain" },
        body: JSON.stringify({ photoGuids: [selectedId] })
      });

      const items = assetJson?.items || {};
      const locations = assetJson?.locations || {};
      const item = items[selectedChecksum];

      if (!item?.url_location || !item?.url_path) {
        return new Response("Failed to resolve fresh download URL from iCloud", { status: 502 });
      }

      const locationObj = locations[item.url_location];
      const host = (locationObj?.hosts && locationObj.hosts[0]) || item.url_location;
      const scheme = locationObj?.scheme || "https";
      const freshImageUrl = `${scheme}://${host}${item.url_path}`;

      return await fetchAndRender(freshImageUrl, token);

    } catch (err) {
      return new Response(`Worker error: ${err.message}`, { status: 500 });
    }
  }
};

async function fetchAndRender(imageUrl, token) {
  const response = await fetch(imageUrl, {
    headers: {
      "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
      "Referer": `https://www.icloud.com/sharedalbum/#${token}`
    }
  });

  if (!response.ok) {
    return new Response(`Apple CDN rejected fetch: Status ${response.status} ${response.statusText} | URL: ${imageUrl}`, { status: 502 });
  }

  return new Response(response.body, {
    headers: {
      "Content-Type": response.headers.get("Content-Type") || "image/jpeg",
      "Content-Disposition": "inline",
      "Cache-Control": "no-store"
    }
  });
}
