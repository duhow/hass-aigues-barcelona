import json

with open("manifest.json") as f:
  manifest = json.load(f)

VERSION = manifest.get("version", "0.0.0")
