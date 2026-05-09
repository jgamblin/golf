#!/usr/bin/env python3
"""Generate social media sharing image for the golf analytics dashboard."""

from PIL import Image, ImageDraw, ImageFont
from pathlib import Path

# Image dimensions: 1200x630 (optimal for most social media)
WIDTH, HEIGHT = 1200, 630
OUTPUT_PATH = Path(__file__).parent.parent / "output" / "golf-analytics-social.png"
OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

# Colors (from the dashboard theme)
BG = "#F2F2F0"
TEXT = "#1E340A"
ACCENT = "#408114"
ACCENT_DARK = "#1B7114"
MUTED = "#4D6E24"

# Create image
img = Image.new("RGB", (WIDTH, HEIGHT), BG)
draw = ImageDraw.Draw(img)

# Try to use nice fonts; fall back to default if unavailable
try:
    title_font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 72)
    subtitle_font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 42)
    tag_font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 28)
except:
    title_font = ImageFont.load_default()
    subtitle_font = ImageFont.load_default()
    tag_font = ImageFont.load_default()

# Draw decorative bars at top and bottom
bar_height = 12
draw.rectangle([(0, 0), (WIDTH, bar_height)], fill=ACCENT)
draw.rectangle([(0, HEIGHT - bar_height), (WIDTH, HEIGHT)], fill=ACCENT)

# Title
title = "Bad at golf."
draw.text((60, 80), title, fill=TEXT, font=title_font)

# Subtitle with emphasis
subtitle = "Great at data."
draw.text((60, 160), subtitle, fill=ACCENT_DARK, font=subtitle_font)

# Feature list
features = [
    "📊 Multi-page R10 analytics",
    "🎯 Gapping & target control",
    "📈 Club path infographics",
    "🧠 AI-powered recommendations",
]

feature_font_size = 24
try:
    feature_font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", feature_font_size)
except:
    feature_font = ImageFont.load_default()

y_offset = 290
line_height = 48
for feature in features:
    draw.text((60, y_offset), feature, fill=MUTED, font=feature_font)
    y_offset += line_height

# URL and CTA at bottom
try:
    url_font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 32)
except:
    url_font = ImageFont.load_default()

draw.text((60, 520), "jgamblin.github.io/golf", fill=ACCENT, font=url_font)
draw.text((WIDTH - 320, 520), "GitHub →", fill=ACCENT_DARK, font=url_font)

# Save
img.save(OUTPUT_PATH)
print(f"✓ Social media image generated: {OUTPUT_PATH}")
