# HungsOS Social Web Apps
# Small, independent app hub. No network calls are made by the ESP32.
# External sites open in a new browser tab; some may require a full browser.

APPS = (
    ("▶️", "YouTube", "https://m.youtube.com", "Video and music"),
    ("♪", "TikTok", "https://www.tiktok.com", "Short videos"),
    ("◎", "Instagram", "https://www.instagram.com", "Photos and reels"),
    ("f", "Facebook", "https://m.facebook.com", "Friends and groups"),
    ("𝕏", "X", "https://x.com", "Posts and updates"),
    ("⌨", "GitHub", "https://github.com", "Code and projects"),
    ("🎵", "SoundCloud", "https://m.soundcloud.com", "Discover music"),
    ("🌐", "Wikipedia", "https://en.m.wikipedia.org", "Quick reference"),
)

def content():
    out = [
        "<h1>Web Apps</h1>",
        "<div class='sub'>Shortcuts to official websites. Internet access is required.</div>",
        "<div class='grid'>",
    ]
    for icon, name, url, description in APPS:
        out.append(
            '<a class="app" href="' + url + '" target="_blank" rel="noopener noreferrer">'
            '<div class="icon blue">' + icon + '</div>'
            '<div class="appname">' + name + '</div>'
            '</a>'
        )
    out.append("</div>")
    out.append(
        "<div class='card'><div class='card-title'>Heads up</div>"
        "<div class='sub'>These are website shortcuts, not native apps. "
        "If a site does not work in an embedded browser, open it in your device's normal browser.</div></div>"
    )
    return "".join(out)
