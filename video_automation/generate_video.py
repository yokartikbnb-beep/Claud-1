"""
YouTube Video Otomasyonu - ENHANCED
Çocuklar İçin 1-10 Sayıları
Animasyonlar: bounce-in · gökkuşağı border · glow efekti · yıldızlar · konfeti · balonlar
"""

import os, math, random
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from moviepy import VideoClip, AudioFileClip, concatenate_videoclips, AudioArrayClip

# ── Config ────────────────────────────────────────────────────────────────────
W, H  = 1280, 720
FPS   = 30
OUT_DIR   = "output"
AUDIO_DIR = os.path.join(OUT_DIR, "audio")
os.makedirs(AUDIO_DIR, exist_ok=True)

NUMBERS = [
    (1,  "Bir",    "#FF4757"),
    (2,  "İki",    "#FF6348"),
    (3,  "Üç",     "#FFA502"),
    (4,  "Dört",   "#2ED573"),
    (5,  "Beş",    "#1E90FF"),
    (6,  "Altı",   "#A55EEA"),
    (7,  "Yedi",   "#FF6EB4"),
    (8,  "Sekiz",  "#00D2D3"),
    (9,  "Dokuz",  "#FF4500"),
    (10, "On",     "#FFD700"),
]

HOOK_SPEECH   = "Merhaba minikler! Hadi birlikte sayalım!"
REVIEW_SPEECH = "Simdi hepsini birlikte tekrar edelim. Hazir misin?"
END_SPEECH    = "Aferin! Cok guzel savdin. Birden Ona kadar savdik!"

# ── Color utils ───────────────────────────────────────────────────────────────
def hex_rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))

def lerp_color(c1, c2, t):
    return tuple(int(c1[i] + (c2[i] - c1[i]) * t) for i in range(3))

RAINBOW = [
    (255, 0, 0), (255, 127, 0), (255, 220, 0),
    (0, 210, 0), (0, 100, 255), (120, 0, 220), (220, 0, 150),
]
def rainbow_color(phase):
    n = len(RAINBOW)
    i = int(phase * n) % n
    j = (i + 1) % n
    return lerp_color(RAINBOW[i], RAINBOW[j], (phase * n) % 1)

# ── Easing ────────────────────────────────────────────────────────────────────
def ease_out_bounce(t):
    t = max(0.0, min(1.0, t))
    if t < 1/2.75:   return 7.5625 * t * t
    elif t < 2/2.75: t -= 1.5/2.75;   return 7.5625*t*t + 0.75
    elif t < 2.5/2.75: t -= 2.25/2.75; return 7.5625*t*t + 0.9375
    else:             t -= 2.625/2.75; return 7.5625*t*t + 0.984375

def ease_out_elastic(t):
    t = max(0.0, min(1.0, t))
    if t in (0, 1): return t
    return pow(2, -10*t) * math.sin((t*10 - 0.75) * (2*math.pi/3)) + 1

# ── Font ──────────────────────────────────────────────────────────────────────
def load_font(size):
    size = max(8, int(size))
    for path in [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    ]:
        if os.path.exists(path):
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()

# ── Drawing helpers ───────────────────────────────────────────────────────────
def draw_star(draw, cx, cy, r, color, n_pts=5, rotation=0.0):
    pts = []
    inner = r * 0.42
    for i in range(n_pts * 2):
        a = rotation + i * math.pi / n_pts - math.pi / 2
        rad = r if i % 2 == 0 else inner
        pts.append((cx + rad * math.cos(a), cy + rad * math.sin(a)))
    if r >= 3:
        draw.polygon(pts, fill=color)

def glow_text(img, text, pos, font, color, glow_col, radius=20):
    """Composites a Gaussian-blurred glow under the text."""
    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gd   = ImageDraw.Draw(glow)
    step = max(2, radius // 5)
    for dx in range(-step*2, step*2+1, step):
        for dy in range(-step*2, step*2+1, step):
            gd.text((pos[0]+dx, pos[1]+dy), text, font=font, fill=(*glow_col, 90))
    glow = glow.filter(ImageFilter.GaussianBlur(radius=radius))
    base = img.convert("RGBA")
    base = Image.alpha_composite(base, glow)
    d2   = ImageDraw.Draw(base)
    d2.text(pos, text, font=font, fill=color)
    return base.convert("RGB")

def draw_rainbow_border(draw, t, thick=14):
    for i in range(W):
        c = rainbow_color(((i / W) + t * 0.25) % 1)
        draw.rectangle([(i, 0),        (i, thick-1)],    fill=c)
        draw.rectangle([(i, H-thick),  (i, H-1)],        fill=c)
    for j in range(H):
        c = rainbow_color(((j / H) + t * 0.25 + 0.5) % 1)
        draw.rectangle([(0, j),        (thick-1, j)],    fill=c)
        draw.rectangle([(W-thick, j),  (W-1, j)],        fill=c)

def draw_twinkle_stars(draw, t, n=20, seed=42):
    random.seed(seed)
    for i in range(n):
        sx = random.randint(40, W-40)
        sy = random.randint(40, H-40)
        phase = random.uniform(0, math.pi*2)
        r = max(3, int(7 + 5 * math.sin(t*3 + phase)))
        ang = t * 1.8 + phase
        brightness = int(180 + 75 * abs(math.sin(t*2 + phase)))
        draw_star(draw, sx, sy, r, (brightness, brightness, brightness), rotation=ang)

def draw_floating_bubbles(draw, color_hex, t, n=12, seed=7):
    r0, g0, b0 = hex_rgb(color_hex)
    random.seed(seed)
    for _ in range(n):
        bx    = random.randint(60, W-60)
        speed = random.uniform(50, 130)
        by0   = random.randint(0, H)
        by    = int((by0 - t * speed) % (H + 100)) - 50
        brad  = random.randint(14, 42)
        light = lambda c: min(255, c + 90)
        draw.ellipse(
            [(bx-brad, by-brad), (bx+brad, by+brad)],
            fill=(light(r0), light(g0), light(b0)),
            outline="white", width=2
        )

def make_gradient_bg(color_hex, t):
    r, g, b = hex_rgb(color_hex)
    pulse = 1.0 + 0.05 * math.sin(t * 1.8)
    r2 = min(255, int(r * 0.35 * pulse))
    g2 = min(255, int(g * 0.35 * pulse))
    b2 = min(255, int(b * 0.35 * pulse))
    img = Image.new("RGB", (W, H))
    draw = ImageDraw.Draw(img)
    for y in range(H):
        ratio = y / H
        cr = int(min(r*pulse, 255) * (1-ratio) + r2 * ratio)
        cg = int(min(g*pulse, 255) * (1-ratio) + g2 * ratio)
        cb = int(min(b*pulse, 255) * (1-ratio) + b2 * ratio)
        draw.line([(0, y), (W, y)], fill=(min(cr,255), min(cg,255), min(cb,255)))
    return img

# ── Number frame (animated) ───────────────────────────────────────────────────
INTRO_DUR = 0.55

def make_number_frame(t, number, name, color_hex):
    img  = make_gradient_bg(color_hex, t)
    draw = ImageDraw.Draw(img)

    draw_rainbow_border(draw, t)
    draw_floating_bubbles(draw, color_hex, t, seed=number*7)
    draw_twinkle_stars(draw, t, n=16, seed=number*13)

    # ── Number bounce-in ─────────────────────────────────────────────────────
    if t < INTRO_DUR:
        scale = ease_out_elastic(t / INTRO_DUR)
    else:
        scale = 1.0 + 0.025 * math.sin(t * 4.5)

    font_num = load_font(int(300 * max(0.05, scale)))
    num_str  = str(number)
    bbox     = draw.textbbox((0, 0), num_str, font=font_num)
    nw, nh   = bbox[2]-bbox[0], bbox[3]-bbox[1]
    nx = (W - nw) // 2
    ny = H // 2 - nh // 2 - 55

    r0, g0, b0 = hex_rgb(color_hex)
    glow_col = (min(r0+80,255), min(g0+80,255), min(b0+80,255))
    img  = glow_text(img, num_str, (nx, ny), font_num, "white", glow_col, radius=22)
    draw = ImageDraw.Draw(img)

    # ── Turkish name ─────────────────────────────────────────────────────────
    name_scale = min(1.0, scale * 1.1)
    font_name  = load_font(int(88 * max(0.05, name_scale)))
    bbox2 = draw.textbbox((0,0), name, font=font_name)
    tw2   = bbox2[2]-bbox2[0]
    img   = glow_text(img, name, ((W-tw2)//2, ny+nh+12), font_name,
                      "white", glow_col, radius=14)
    draw  = ImageDraw.Draw(img)

    # ── Circles pop in one by one ─────────────────────────────────────────────
    circles_t = max(0.0, t - INTRO_DUR) / 0.65
    spacing   = 68 if number <= 9 else 62
    total_w   = number * spacing
    cx_start  = W//2 - total_w//2 + spacing//2
    cy_c      = H - 72

    for i in range(number):
        c_progress = max(0.0, circles_t * number - i)
        c_scale    = ease_out_bounce(min(c_progress, 1.0))
        cr         = max(1, int(26 * c_scale))
        cx_i       = cx_start + i * spacing
        phase      = (i / max(number, 1) + t * 0.12) % 1
        c_col      = rainbow_color(phase)
        draw.ellipse([(cx_i-cr, cy_c-cr), (cx_i+cr, cy_c+cr)],
                     fill=c_col, outline="white", width=3)
        if c_scale > 0.55:
            f_ci = load_font(int(20 * c_scale))
            cs   = str(i+1)
            cb   = draw.textbbox((0,0), cs, font=f_ci)
            cw   = (cb[2]-cb[0]); ch = (cb[3]-cb[1])
            draw.text((cx_i - cw//2, cy_c - ch//2), cs, font=f_ci, fill="white")

    # ── Corner sparkles ───────────────────────────────────────────────────────
    if t > INTRO_DUR:
        st = t - INTRO_DUR
        corners = [(88, 88), (W-88, 88), (88, H-88), (W-88, H-88)]
        for idx, (sx, sy) in enumerate(corners):
            ph    = idx * math.pi / 2
            r_sp  = max(3, int(14 + 7 * math.sin(st * 5 + ph)))
            angle = st * 2.2 + ph
            col   = rainbow_color((st * 0.2 + ph/6) % 1)
            draw_star(draw, sx, sy, r_sp, col, rotation=angle)

    return np.array(img)

# ── Hook frame ────────────────────────────────────────────────────────────────
def make_hook_frame(t, text="Hadi Birlikte Sayalim!"):
    img  = Image.new("RGB", (W, H), (18, 10, 42))
    draw = ImageDraw.Draw(img)

    # Animated gradient overlay
    for y in range(H):
        ratio = y / H
        hue_shift = t * 0.15
        c = rainbow_color((ratio * 0.4 + hue_shift) % 1)
        r2 = int(18 + c[0] * 0.25)
        g2 = int(10 + c[1] * 0.25)
        b2 = int(42 + c[2] * 0.25)
        draw.line([(0, y), (W, y)], fill=(min(r2,255), min(g2,255), min(b2,255)))

    draw_rainbow_border(draw, t, thick=16)
    draw_twinkle_stars(draw, t, n=30, seed=55)

    # Floating colorful bubbles
    random.seed(99)
    for i in range(10):
        bx    = random.randint(80, W-80)
        speed = random.uniform(50, 110)
        by    = int((random.randint(0, H) - t * speed) % (H+80)) - 40
        brad  = random.randint(18, 48)
        col   = rainbow_color((i/10 + t*0.1) % 1)
        draw.ellipse([(bx-brad,by-brad),(bx+brad,by+brad)], fill=col)

    progress = min(1.0, t / 0.5)
    s = max(0.05, ease_out_bounce(progress))
    font = load_font(int(92 * s))
    bbox = draw.textbbox((0,0), text, font=font)
    tw, th = bbox[2]-bbox[0], bbox[3]-bbox[1]
    img = glow_text(img, text, ((W-tw)//2, (H-th)//2), font,
                    "white", (180, 160, 255), radius=22)
    return np.array(img)

# ── Review grid frame ─────────────────────────────────────────────────────────
def make_review_frame(t):
    img  = Image.new("RGB", (W, H), (12, 5, 30))
    draw = ImageDraw.Draw(img)

    for y in range(H):
        c = rainbow_color((y/H * 0.3 + t*0.1) % 1)
        r2 = int(12 + c[0]*0.18)
        g2 = int(5  + c[1]*0.18)
        b2 = int(30 + c[2]*0.18)
        draw.line([(0,y),(W,y)], fill=(min(r2,255), min(g2,255), min(b2,255)))

    draw_rainbow_border(draw, t, thick=16)
    draw_twinkle_stars(draw, t, n=25, seed=77)

    title = "Hepsini Sayalim!"
    f_title = load_font(68)
    bt = draw.textbbox((0,0), title, font=f_title)
    tw = bt[2]-bt[0]
    img  = glow_text(img, title, ((W-tw)//2, 24), f_title,
                     "white", (200,180,255), radius=14)
    draw = ImageDraw.Draw(img)

    cols, rows = 5, 2
    cell_w = W // cols
    cell_h = (H - 130) // rows

    for idx, (num, name, color) in enumerate(NUMBERS):
        col_i = idx % cols
        row_i = idx // cols
        cx = col_i * cell_w + cell_w // 2
        cy = 134 + row_i * cell_h + cell_h // 2

        delay    = idx * 0.14
        progress = max(0.0, min(1.0, (t - delay) / 0.35))
        r_cell   = max(1, int(52 * ease_out_bounce(progress)))

        c_col = rainbow_color((idx/10 + t*0.09) % 1)
        draw.ellipse([(cx-r_cell, cy-r_cell), (cx+r_cell, cy+r_cell)],
                     fill=c_col, outline="white", width=3)

        if progress > 0.55:
            f_n = load_font(int(48 * progress))
            ns  = str(num)
            nb  = draw.textbbox((0,0), ns, font=f_n)
            nw  = nb[2]-nb[0]; nh = nb[3]-nb[1]
            draw.text((cx-nw//2, cy-nh//2-8), ns, font=f_n, fill="white")
            f_nm = load_font(int(22 * progress))
            mb   = draw.textbbox((0,0), name, font=f_nm)
            mw   = mb[2]-mb[0]
            draw.text((cx-mw//2, cy+28), name, font=f_nm, fill="white")

    return np.array(img)

# ── End / confetti frame ──────────────────────────────────────────────────────
def make_end_frame(t):
    img  = Image.new("RGB", (W, H), (10, 5, 28))
    draw = ImageDraw.Draw(img)

    # Gradient
    for y in range(H):
        c = rainbow_color((y/H * 0.5 + t*0.18) % 1)
        draw.line([(0,y),(W,y)],
                  fill=(min(10+int(c[0]*0.22),255), min(5+int(c[1]*0.22),255),
                        min(28+int(c[2]*0.22),255)))

    draw_rainbow_border(draw, t, thick=20)

    # Confetti
    random.seed(44)
    for i in range(70):
        cx    = random.randint(0, W)
        speed = random.uniform(90, 210)
        cy    = int((random.randint(-H//2, H) + t * speed) % (H+100))
        cw    = random.randint(8, 22)
        angle = t * random.uniform(1.5, 4.5) + random.uniform(0, math.pi*2)
        col   = rainbow_color((i/70 + t*0.18) % 1)
        pts   = [
            (cx + cw*math.cos(angle),            cy + cw*math.sin(angle)),
            (cx + cw*math.cos(angle+math.pi/2),  cy + cw*math.sin(angle+math.pi/2)),
            (cx - cw*math.cos(angle),             cy - cw*math.sin(angle)),
            (cx - cw*math.cos(angle+math.pi/2),  cy - cw*math.sin(angle+math.pi/2)),
        ]
        draw.polygon(pts, fill=col)

    draw_twinkle_stars(draw, t, n=22, seed=33)

    # Pulsing text
    pulse = 1.0 + 0.06 * math.sin(t * 6)
    f_big = load_font(int(118 * pulse))
    f_sub = load_font(64)
    text1 = "Aferin!"
    text2 = "Cok guzel savdin!"

    b1 = draw.textbbox((0,0), text1, font=f_big)
    tw1, th1 = b1[2]-b1[0], b1[3]-b1[1]
    img  = glow_text(img, text1, ((W-tw1)//2, H//2-th1-18),
                     f_big, "yellow", (255,200,0), radius=30)
    draw = ImageDraw.Draw(img)

    b2   = draw.textbbox((0,0), text2, font=f_sub)
    tw2  = b2[2]-b2[0]
    img  = glow_text(img, text2, ((W-tw2)//2, H//2+24),
                     f_sub, "white", (200,200,255), radius=16)
    return np.array(img)

# ── TTS (espeak-ng offline) ───────────────────────────────────────────────────
def make_tts(text, filename):
    wav = filename.replace(".mp3", ".wav")
    path = os.path.join(AUDIO_DIR, wav)
    if not os.path.exists(path):
        os.system(f'espeak-ng -v tr -s 130 -p 60 -w "{path}" "{text}" 2>/dev/null')
    return path

# ── Clip builders ─────────────────────────────────────────────────────────────
def video_clip(frame_fn, audio_path, min_dur=3.0, pad=0.6):
    aud = AudioFileClip(audio_path)
    dur = max(aud.duration + pad, min_dur)
    return VideoClip(frame_fn, duration=dur).with_fps(FPS).with_audio(aud)

# ── Main pipeline ─────────────────────────────────────────────────────────────
def build_video():
    print("▶  Sesler üretiliyor (espeak-ng)...")
    hook_audio   = make_tts(HOOK_SPEECH,   "hook.mp3")
    review_audio = make_tts(REVIEW_SPEECH, "review.mp3")
    end_audio    = make_tts(END_SPEECH,    "end.mp3")
    number_audios = [
        make_tts(f"{name} {num}", f"number_{num:02d}.mp3")
        for num, name, _ in NUMBERS
    ]

    print("▶  Animasyonlu klipleri render ediyorum...")
    clips = []

    # Hook
    clips.append(video_clip(make_hook_frame, hook_audio, min_dur=3.5))

    # Sayılar
    for (num, name, color), audio in zip(NUMBERS, number_audios):
        print(f"   {num:>2} – {name}")
        fn = lambda t, n=num, nm=name, c=color: make_number_frame(t, n, nm, c)
        clips.append(video_clip(fn, audio, min_dur=3.0, pad=0.8))

    # Tekrar grid
    clips.append(video_clip(make_review_frame, review_audio, min_dur=5.0, pad=0.8))

    # Bitiş konfeti
    clips.append(video_clip(make_end_frame, end_audio, min_dur=4.5, pad=0.8))

    print("▶  Tüm klipleri birleştirip video yazılıyor...")
    final    = concatenate_videoclips(clips, method="compose")
    out_path = os.path.join(OUT_DIR, "sayilar_1_10.mp4")
    final.write_videofile(out_path, fps=FPS, codec="libx264",
                          audio_codec="aac", logger="bar")
    final.close()
    print(f"\n✅ Video hazır → {out_path}  ({final.duration:.1f} saniye)")
    return out_path

if __name__ == "__main__":
    build_video()
