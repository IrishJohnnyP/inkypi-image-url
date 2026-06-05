# InkyPi Image URL

An InkyPi plugin that fetches an image from a URL and displays it on your e-paper screen. Useful for dashboards, status boards, weather maps, or any remotely hosted image you want to cycle through on your InkyPi frame.

_Image URL_ is a plugin for [InkyPi](https://github.com/fatihak/InkyPi) that pulls an **PNG**, **JPG**, and **JPEG** image from a valid URL and displays it on your InkyPi frame.

## Install

Use the InkyPi plugin installer with the plugin ID and this repository URL:

```bash
inkypi plugin install image_url https://github.com/shadal18/inkypi-image-url
```

## Update

To update the plugin on your InkyPi device:

1. SSH into your InkyPi host.
2. Change into the plugin directory:
   ```bash
   cd ~/InkyPi/src/plugins/image_url
   ```
3. Pull the latest changes and restart:
   ```bash
   git pull origin main && \
   if [ -d image_url ]; then \
     rsync -a image_url/ ./ && \
     rm -rf image_url; \
   fi && \
   sudo systemctl restart inkypi.service
   ```

If you don't see your changes after updating:

- Confirm you are in the correct plugin folder.
- Clear your browser cache or hard-refresh the InkyPi web UI.
- Check the InkyPi logs for any plugin errors.

## Requirements

- A valid URL pointing to a publicly accessible image.
- Network access from the InkyPi device to the image host.
- No API keys required.

## Features

- Displays any image hosted at a URL directly on your InkyPi e-paper display.
- Supports **PNG**, **JPG**, and **JPEG** image formats.
- Automatically scales and fits the image to your display dimensions.
- No external API account needed — just paste a URL and go.

## Settings

| Setting   | Description                                                                             |
| --------- | --------------------------------------------------------------------------------------- |
| Image URL | The full URL to the image you want to display (must end in `.png`, `.jpg`, or `.jpeg`). |

## Supported Formats

| Format | Extension       |
| ------ | --------------- |
| PNG    | `.png`          |
| JPEG   | `.jpg`, `.jpeg` |

## Troubleshooting

**Image does not appear:**

- Make sure the URL is publicly accessible (no login, no paywall).
- Confirm the URL points directly to an image file, not an HTML page.
- Check that the file extension is `.png`, `.jpg`, or `.jpeg`.

**Display looks stretched or cropped:**

- The plugin scales the image to fit your InkyPi display. Images closest to your display's native aspect ratio will look best.

## Repository

[https://github.com/shadal18/inkypi-image-url](https://github.com/shadal18/inkypi-image-url)

## Screenshots

<p align="center">
  <img src="screenshots/example.png" width="45%" />
  <img src="screenshots/settings.png" width="45%" />
</p>
