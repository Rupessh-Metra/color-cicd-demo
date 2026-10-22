"""Color CI/CD demo app.

Every pipeline run passes a new BUILD_NUMBER into the image, and the page
background colour is calculated from it. So every push = a new colour on the
live site, which makes each deployment easy to see.
"""

import colorsys
import os
from datetime import datetime, timezone

from flask import Flask, jsonify, render_template_string

app = Flask(__name__)

APP_VERSION = os.getenv("APP_VERSION", "local")
BUILD_NUMBER = os.getenv("BUILD_NUMBER", "0")
STARTED_AT = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

GOLDEN_ANGLE = 137.508  # degrees - consecutive builds land far apart on the colour wheel


def color_for_build(build_number):
    """Return a hex colour for a build number. Each new build gets a clearly different colour."""
    try:
        number = int(build_number)
    except (TypeError, ValueError):
        number = 0
    hue = (number * GOLDEN_ANGLE) % 360
    red, green, blue = colorsys.hls_to_rgb(hue / 360, 0.38, 0.65)
    return "#{:02x}{:02x}{:02x}".format(round(red * 255), round(green * 255), round(blue * 255))


PAGE = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta http-equiv="refresh" content="10">
  <title>Color CI/CD Demo - build {{ build }}</title>
  <style>
    body { margin: 0; min-height: 100vh; display: flex; align-items: center; justify-content: center;
           background: {{ color }}; color: #fff; font-family: Arial, Helvetica, sans-serif; }
    main { text-align: center; padding: 40px; }
    h1 { font-size: 56px; margin: 0 0 12px; }
    .swatch { font-size: 22px; opacity: .9; margin-bottom: 32px; }
    dl { display: inline-grid; grid-template-columns: auto auto; gap: 8px 24px; text-align: left;
         background: rgba(0, 0, 0, .25); padding: 20px 28px; border-radius: 12px; font-size: 18px; }
    dt { opacity: .75; }
    dd { margin: 0; font-weight: bold; font-family: monospace; }
    footer { margin-top: 28px; opacity: .75; font-size: 14px; }
  </style>
</head>
<body>
  <main>
    <h1>Hello this is the demo for stride program from the devops team!</h1>
    <div class="swatch">This build's colour is <b>{{ color }}</b></div>
    <dl>
      <dt>Build number</dt><dd>#{{ build }}</dd>
      <dt>Commit</dt><dd>{{ version }}</dd>
      <dt>Container started</dt><dd>{{ started }}</dd>
    </dl>
    <footer>Demo push 2 - deployed by GitHub Actions</footer>
  </main>
</body>
</html>"""


@app.route("/")
def home():
    return render_template_string(
        PAGE,
        color=color_for_build(BUILD_NUMBER),
        build=BUILD_NUMBER,
        version=APP_VERSION,
        started=STARTED_AT,
    )


@app.route("/health")
def health():
    return jsonify(status="ok")


@app.route("/api/info")
def info():
    return jsonify(
        build=BUILD_NUMBER,
        version=APP_VERSION,
        color=color_for_build(BUILD_NUMBER),
        started=STARTED_AT,
    )

