# Deploy the HùngOS companion page on Render

This folder is a static information page. It does not connect to or control the ESP32.

## Render setup

1. Sign in to Render and choose **New → Static Site**.
2. Connect the GitHub repository `NaN-c-pixel/Phone`.
3. Select the `main` branch.
4. Set **Root Directory** to `website`.
5. Leave **Build Command** empty (there is no build step).
6. Set **Publish Directory** to `.`.
7. Choose the free option if prompted, then create the site.

Render will provide an `onrender.com` URL after the first deploy. Future commits to `main` will trigger redeploys.

## Notes

- Static sites are free to deploy on Render.
- This page is public. Do not put Wi-Fi passwords, private IP addresses, API keys, or other secrets in it.
- The ESP32's browser interface remains on your local network; this website is only a project landing page.
