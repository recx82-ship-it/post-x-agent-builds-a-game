"""Render the video's first two segments as PNG frames with PIL.

Segment A (0-4s): the one prompt, typed out in a chat-style frame.
Segment B (4-12s): the agent working — a terminal with code streaming in
and the entry files appearing as they are written.
Deterministic: fixed text, fixed timing, no randomness.
"""
import textwrap
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
OUT = HERE / "frames"
OUT.mkdir(exist_ok=True)
FONTS = HERE.parent / "assets" / "fonts"

W, H, FPS = 1080, 1920, 30
BG = (5, 6, 15)
PANEL = (13, 16, 36)
PANEL_EDGE = (38, 58, 110)
GREEN = (0, 255, 194)
TEXT = (232, 246, 255)
MUTED = (139, 147, 184)
AMBER = (255, 214, 64)
MAGENTA = (196, 28, 131)

INTER = str(FONTS / "Inter-Bold.ttf")
MONO = str(FONTS / "JetBrainsMono-Bold.ttf")


def font(path, size):
    return ImageFont.truetype(path, size)


def base():
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)
    # faint grid dots, like the game's dark grid
    for x in range(0, W, 90):
        for y in range(0, H, 90):
            d.ellipse([x - 1, y - 1, x + 1, y + 1], fill=(16, 20, 42))
    return img, d


def rounded_panel(d, box, fill, edge):
    d.rounded_rectangle(box, radius=28, fill=fill, outline=edge, width=2)


PROMPT = (
    "Build me a tiny browser game: a neon snake game on a dark grid. "
    "Arrow keys to steer, eat the glowing food to grow and score points, "
    "get faster every time you eat, game over screen with your score and "
    "press R to restart. One HTML file, no libraries."
)

TERMINAL_LINES = [
    ("$ ", "agent: building neon snake…", GREEN),
    ("", "  canvas 640×640 · 20×20 grid", MUTED),
    ("", "  snake = [{x:10,y:10}, …]", TEXT),
    ("", "  food glows · +10 pts a bite", TEXT),
    ("", "  speed += 6 ms faster each bite", TEXT),
    ("", "  game over → score · press R", TEXT),
    ("✓ ", "game.html written — 8.4 KB", GREEN),
    ("✓ ", "main.ts written — copies POST.json", GREEN),
    ("$ ", "rendering video…", GREEN),
]


def segment_a():
    """0-4s: the prompt types itself into a chat bubble."""
    f_title = font(INTER, 40)
    f_body = font(INTER, 42)
    f_small = font(INTER, 30)
    lines = textwrap.wrap(PROMPT, width=30)
    total_chars = len(PROMPT)
    for i in range(4 * FPS):
        t = i / FPS
        img, d = base()
        # header
        d.text((80, 120), "ONE PROMPT", font=f_small, fill=GREEN)
        d.text((80, 170), "You  ->  your AI agent", font=f_title, fill=TEXT)
        # chat bubble
        rounded_panel(d, [60, 280, 1020, 1050], PANEL, PANEL_EDGE)
        d.ellipse([100, 330, 150, 380], fill=GREEN)
        d.text((175, 322), "you", font=f_small, fill=MUTED)
        # typed characters so far (ease in over 3.4s, hold the rest)
        shown = int(total_chars * min(1.0, t / 3.4))
        shown_text = PROMPT[:shown]
        wrapped = textwrap.wrap(shown_text, width=30)
        y = 420
        for ln in wrapped:
            d.text((100, y), ln, font=f_body, fill=TEXT)
            y += 62
        # blinking caret at the end of the typed text
        if shown < total_chars and int(t * 2) % 2 == 0:
            last = wrapped[-1] if wrapped else ""
            cx = 100 + f_body.getlength(last) + 8
            d.rectangle([cx, y - 62 + 6, cx + 5, y - 8], fill=GREEN)
        # footer hint
        d.text((80, 1150), "…and the agent builds the whole game.", font=f_small, fill=MUTED)
        img.save(OUT / f"a_{i:04d}.png")


def segment_b():
    """4-12s: terminal with code streaming in; files appear on the side."""
    f_term = font(MONO, 30)
    f_title = font(INTER, 40)
    f_small = font(INTER, 30)
    f_file = font(MONO, 34)
    total = len(TERMINAL_LINES)
    for i in range(8 * FPS):
        t = i / FPS
        img, d = base()
        d.text((80, 120), "THE AGENT GETS TO WORK", font=f_small, fill=GREEN)
        d.text((80, 170), "Writing the game, live.", font=f_title, fill=TEXT)
        # terminal window
        rounded_panel(d, [60, 280, 1020, 1180], (8, 10, 24), PANEL_EDGE)
        d.ellipse([100, 310, 124, 334], fill=(255, 95, 86))
        d.ellipse([140, 310, 164, 334], fill=(255, 189, 46))
        d.ellipse([180, 310, 204, 334], fill=(39, 201, 63))
        d.text((240, 306), "agent — building neon-snake", font=f_small, fill=MUTED)
        # lines appear one every ~0.7s
        n = min(total, int(t / 0.7) + 1)
        y = 380
        for j in range(n):
            pre, txt, col = TERMINAL_LINES[j]
            d.text((100, y), pre + txt, font=f_term, fill=col)
            y += 52
        # file list: game.html appears at 2.5s, main.ts at 5s
        rounded_panel(d, [60, 1240, 1020, 1620], PANEL, PANEL_EDGE)
        d.text((100, 1280), "files", font=f_small, fill=MUTED)
        if t >= 2.5:
            d.text((100, 1340), "▸ game.html", font=f_file, fill=GREEN)
            d.text((700, 1340), "8.4 KB ✓", font=f_file, fill=MUTED)
        if t >= 5.0:
            d.text((100, 1420), "▸ main.ts", font=f_file, fill=GREEN)
            d.text((700, 1420), "0.9 KB ✓", font=f_file, fill=MUTED)
        if t >= 6.5:
            d.text((100, 1500), "▸ video.mp4  rendering…", font=f_file, fill=AMBER)
        img.save(OUT / f"b_{i:04d}.png")


if __name__ == "__main__":
    segment_a()
    segment_b()
    print("frames written:", len(list(OUT.glob('*.png'))))
