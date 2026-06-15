"""
YouTube Video Otomasyonu: Çocuklar İçin 1-10 Sayıları
Üretilen video: renkli kart animasyonu + Türkçe TTS seslendirme
"""

import os
import math
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from moviepy import (
    ImageClip, AudioFileClip, concatenate_videoclips,
    CompositeVideoClip, AudioArrayClip
)

# ── Ayarlar ───────────────────────────────────────────────────────────────────
WIDTH, HEIGHT = 1280, 720
FPS = 30
OUT_DIR = "output"
AUDIO_DIR = os.path.join(OUT_DIR, "audio")
FRAME_DIR = os.path.join(OUT_DIR, "frames")
os.makedirs(AUDIO_DIR, exist_ok=True)
os.makedirs(FRAME_DIR, exist_ok=True)

# Her sayı için isim ve renk
NUMBERS = [
    (1,  "Bir",    "#FF6B6B"),
    (2,  "İki",    "#FF9F43"),
    (3,  "Üç",     "#FECA57"),
    (4,  "Dört",   "#48DBFB"),
    (5,  "Beş",    "#FF9FF3"),
    (6,  "Altı",   "#54A0FF"),
    (7,  "Yedi",   "#5F27CD"),
    (8,  "Sekiz",  "#00D2D3"),
    (9,  "Dokuz",  "#1DD1A1"),
    (10, "On",     "#C8D6E5"),
]

HOOK_TEXT   = "Hadi birlikte sayalım!"
REVIEW_TEXT = "Tekrar edelim:"
END_TEXT    = "Aferin! Çok güzel saydın! 🎉"

# Seslendirme metinleri
HOOK_SPEECH   = "Merhaba minikler! Hadi birlikte sayalım!"
REVIEW_SPEECH = "Şimdi hepsini birlikte tekrar edelim. Hazır mısın?"
END_SPEECH    = "Aferin! Çok güzel saydın. Bir'den On'a kadar saydık!"


# ── Yardımcı: Gradyan arka plan ───────────────────────────────────────────────
def hex_to_rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))


def make_gradient_bg(color_hex):
    """Seçilen rengin açık→koyu dikey gradyanı."""
    r, g, b = hex_to_rgb(color_hex)
    img = Image.new("RGB", (WIDTH, HEIGHT))
    draw = ImageDraw.Draw(img)
    for y in range(HEIGHT):
        ratio = y / HEIGHT
        cr = int(r + (r * 0.4) * (1 - ratio))
        cg = int(g + (g * 0.4) * (1 - ratio))
        cb = int(b + (b * 0.4) * (1 - ratio))
        cr, cg, cb = min(cr, 255), min(cg, 255), min(cb, 255)
        draw.line([(0, y), (WIDTH, y)], fill=(cr, cg, cb))
    return img


# ── Yardımcı: Font yükleme ────────────────────────────────────────────────────
def load_font(size):
    for path in [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        "/usr/share/fonts/TTF/DejaVuSans-Bold.ttf",
    ]:
        if os.path.exists(path):
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


# ── Kare üreticileri ──────────────────────────────────────────────────────────
def draw_circles(draw, color_hex, count, cx, cy, radius=28, spacing=70):
    """Alt kısımda sembolik daireler (sayı kadar)."""
    r, g, b = hex_to_rgb(color_hex)
    circle_color = (max(r - 60, 0), max(g - 60, 0), max(b - 60, 0))
    total_w = count * spacing
    start_x = cx - total_w // 2 + spacing // 2
    for i in range(count):
        x = start_x + i * spacing
        draw.ellipse(
            [(x - radius, cy - radius), (x + radius, cy + radius)],
            fill=circle_color, outline="white", width=3
        )


def make_number_frame(number, name, color_hex):
    img = make_gradient_bg(color_hex)
    draw = ImageDraw.Draw(img)

    # Büyük rakam
    font_num = load_font(320)
    num_str = str(number)
    bbox = draw.textbbox((0, 0), num_str, font=font_num)
    nw, nh = bbox[2] - bbox[0], bbox[3] - bbox[1]
    nx = (WIDTH - nw) // 2
    ny = HEIGHT // 2 - nh // 2 - 60

    # Rakam gölgesi
    draw.text((nx + 6, ny + 6), num_str, font=font_num, fill=(0, 0, 0, 80))
    draw.text((nx, ny), num_str, font=font_num, fill="white")

    # Türkçe isim
    font_name = load_font(90)
    bbox2 = draw.textbbox((0, 0), name, font=font_name)
    tw = bbox2[2] - bbox2[0]
    draw.text(((WIDTH - tw) // 2 + 3, ny + nh + 18), name, font=font_name, fill=(0, 0, 0, 100))
    draw.text(((WIDTH - tw) // 2, ny + nh + 15), name, font=font_name, fill="white")

    # Sembolik daireler (max 10 tanesi sığar)
    if number <= 10:
        draw_circles(draw, color_hex, number, WIDTH // 2, HEIGHT - 70)

    path = os.path.join(FRAME_DIR, f"number_{number:02d}.png")
    img.save(path)
    return path


def make_text_frame(text, bg_color="#2C3E50"):
    img = make_gradient_bg(bg_color)
    draw = ImageDraw.Draw(img)
    font = load_font(80)
    bbox = draw.textbbox((0, 0), text, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    draw.text(((WIDTH - tw) // 2 + 3, (HEIGHT - th) // 2 + 3), text, font=font, fill=(0, 0, 0, 80))
    draw.text(((WIDTH - tw) // 2, (HEIGHT - th) // 2), text, font=font, fill="white")
    path = os.path.join(FRAME_DIR, f"text_{text[:10].replace(' ','_')}.png")
    img.save(path)
    return path


def make_review_frame(colors):
    """1-10 arası tüm rakamları küçük gösterir."""
    img = make_gradient_bg("#2C3E50")
    draw = ImageDraw.Draw(img)
    font_big = load_font(55)
    font_sm  = load_font(28)

    title = "1'den 10'a Tekrar!"
    bbox = draw.textbbox((0, 0), title, font=font_big)
    tw = bbox[2] - bbox[0]
    draw.text(((WIDTH - tw) // 2, 30), title, font=font_big, fill="white")

    cols, rows = 5, 2
    cell_w = WIDTH // cols
    cell_h = (HEIGHT - 120) // rows

    for idx, (num, name, color) in enumerate(NUMBERS):
        col = idx % cols
        row = idx // cols
        cx = col * cell_w + cell_w // 2
        cy = 130 + row * cell_h + cell_h // 2

        r, g, b = hex_to_rgb(color)
        draw.ellipse([(cx - 50, cy - 50), (cx + 50, cy + 50)],
                     fill=(r, g, b), outline="white", width=3)

        n_str = str(num)
        bbox = draw.textbbox((0, 0), n_str, font=font_big)
        nw = bbox[2] - bbox[0]
        nh = bbox[3] - bbox[1]
        draw.text((cx - nw // 2, cy - nh // 2 - 10), n_str, font=font_big, fill="white")

        bbox2 = draw.textbbox((0, 0), name, font=font_sm)
        tw2 = bbox2[2] - bbox2[0]
        draw.text((cx - tw2 // 2, cy + 45), name, font=font_sm, fill="white")

    path = os.path.join(FRAME_DIR, "review.png")
    img.save(path)
    return path


# ── Ses üreticileri ───────────────────────────────────────────────────────────
def make_tts(text, filename, lang="tr"):
    """espeak-ng ile offline Türkçe TTS üretir (WAV olarak kaydeder)."""
    wav_filename = filename.replace(".mp3", ".wav")
    path = os.path.join(AUDIO_DIR, wav_filename)
    if not os.path.exists(path):
        os.system(
            f'espeak-ng -v {lang} -s 130 -p 60 '
            f'-w "{path}" "{text}" 2>/dev/null'
        )
    return path


def silent_audio(duration, fps=44100):
    """MoviePy AudioArrayClip olarak sessiz ses."""
    samples = int(duration * fps)
    arr = np.zeros((samples, 2), dtype=np.float32)
    return AudioArrayClip(arr, fps=fps)


def get_audio_duration(path):
    clip = AudioFileClip(path)
    d = clip.duration
    clip.close()
    return d


# ── Klip birleştirici ─────────────────────────────────────────────────────────
def make_clip(image_path, audio_path, min_duration=2.5, pad=0.5):
    audio = AudioFileClip(audio_path)
    duration = max(audio.duration + pad, min_duration)
    img_clip = ImageClip(image_path, duration=duration)
    img_clip = img_clip.with_audio(audio)
    return img_clip


def make_clip_no_audio(image_path, duration=2.0):
    return ImageClip(image_path, duration=duration)


# ── Ana pipeline ──────────────────────────────────────────────────────────────
def build_video():
    print("▶  Kareler oluşturuluyor...")
    hook_frame    = make_text_frame(HOOK_TEXT,   "#1A1A2E")
    review_grid   = make_review_frame([c for _, _, c in NUMBERS])
    review_frame  = make_text_frame(REVIEW_TEXT, "#2C3E50")
    end_frame     = make_text_frame(END_TEXT,    "#0F3460")

    number_frames = []
    for num, name, color in NUMBERS:
        number_frames.append(make_number_frame(num, name, color))

    print("▶  Sesler üretiliyor (TTS)...")
    hook_audio   = make_tts(HOOK_SPEECH,   "hook.mp3")
    review_audio = make_tts(REVIEW_SPEECH, "review.mp3")
    end_audio    = make_tts(END_SPEECH,    "end.mp3")

    number_audios = []
    for num, name, _ in NUMBERS:
        speech = f"{name}... {num}"
        number_audios.append(make_tts(speech, f"number_{num:02d}.mp3"))

    print("▶  Klipleri birleştiriyorum...")
    clips = []

    # Hook
    clips.append(make_clip(hook_frame, hook_audio, min_duration=3.0))

    # Sayılar
    for frame, audio in zip(number_frames, number_audios):
        clips.append(make_clip(frame, audio, min_duration=2.5, pad=0.8))

    # Gözden geçirme
    clips.append(make_clip(review_frame, review_audio, min_duration=3.0))
    clips.append(make_clip_no_audio(review_grid, duration=4.0))

    # Bitiş
    clips.append(make_clip(end_frame, end_audio, min_duration=3.0))

    print("▶  Video render ediliyor...")
    final = concatenate_videoclips(clips, method="compose")
    out_path = os.path.join(OUT_DIR, "sayilar_1_10.mp4")
    final.write_videofile(
        out_path,
        fps=FPS,
        codec="libx264",
        audio_codec="aac",
        logger="bar",
    )
    final.close()
    print(f"\n✅ Video hazır: {out_path}")
    print(f"   Toplam süre : {final.duration:.1f} saniye")
    return out_path


if __name__ == "__main__":
    build_video()
