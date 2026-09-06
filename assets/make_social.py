#!/usr/bin/env python3
"""Regenerate assets/social-preview.png from assets/example.png."""
import os
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
W, H = 1280, 640
BG = (13, 17, 23)
ACCENT = (63, 214, 143)
FZ = "/usr/share/fonts/truetype/dejavu/"
f_sans_b = lambda s: ImageFont.truetype(FZ + "DejaVuSans-Bold.ttf", s)
f_mono_b = lambda s: ImageFont.truetype(FZ + "DejaVuSansMono-Bold.ttf", s)

canvas = Image.new("RGB", (W, H), BG)

# Full example screenshot, shown in its entirety, right-aligned.
shot = Image.open(os.path.join(HERE, "example.png")).convert("RGB")
sw = int(shot.width * H / shot.height)
shot = shot.resize((sw, H), Image.LANCZOS)
canvas.paste(shot, (W - sw, 0))

# Left-to-right dark scrim so the text stays legible over the screenshot.
scrim = Image.new("L", (W, H), 0)
sd = ImageDraw.Draw(scrim)
for x in range(W):
    t = x / W
    a = 255 if t < 0.30 else max(0, int(255 * (1 - (t - 0.30) / 0.45)))
    sd.line([(x, 0), (x, H)], fill=a)
canvas = Image.composite(Image.new("RGB", (W, H), BG), canvas, scrim)

d = ImageDraw.Draw(canvas)
x0 = 64

# Badge
bt = "LINUX  ·  XFCE4"
bf = f_mono_b(20)
bb = d.textbbox((0, 0), bt, font=bf)
pad = 16
d.rounded_rectangle([x0, 60, x0 + (bb[2] - bb[0]) + pad * 2, 60 + (bb[3] - bb[1]) + pad * 2],
                    radius=20, outline=ACCENT, width=2)
d.text((x0 + pad, 60 + pad - bb[1]), bt, font=bf, fill=ACCENT)

d.text((x0 - 4, 120), "graytoggle", font=f_sans_b(96), fill=(255, 255, 255))
d.text((x0, 232), "Instant grayscale mode for", font=f_sans_b(30), fill=(230, 233, 238))
d.text((x0, 272), "the Linux desktop.", font=f_sans_b(30), fill=(230, 233, 238))
d.text((x0, 326), "One command. No hardware.", font=f_sans_b(24), fill=(150, 156, 165))
d.text((x0, 360), "Pure software.", font=f_sans_b(24), fill=(150, 156, 165))

cf = f_mono_b(24)
ct = "$ graytoggle"
cb = d.textbbox((0, 0), ct, font=cf)
d.rounded_rectangle([x0, 414, x0 + (cb[2] - cb[0]) + 40, 414 + (cb[3] - cb[1]) + 28],
                    radius=8, outline=(48, 54, 61), width=1)
d.text((x0 + 20, 414 + 14 - cb[1]), ct, font=cf, fill=ACCENT)

canvas.save(os.path.join(HERE, "social-preview.png"))
print("wrote social-preview.png")
