import json
import os

try:
    with open(os.path.join(os.path.dirname(__file__), "manifest.json")) as f:
        manifest = json.load(f)
except FileNotFoundError:
    manifest = {}

VERSION = manifest.get("version", "0.0.0")
