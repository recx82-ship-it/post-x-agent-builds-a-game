"""Capture real Neon Snake gameplay with headless Chromium (Playwright).

Steers the snake toward the food with a greedy driver that reads the
game's own debug hook, so the score visibly climbs. Records the viewport
as video; the render script crops/scales it into the 9:16 frame.
"""
import asyncio
import sys
from pathlib import Path

from playwright.async_api import async_playwright

HERE = Path(__file__).resolve().parent
GAME = (HERE.parent / "game.html").as_uri()
OUT = HERE / "gameplay"
OUT.mkdir(exist_ok=True)

KEYS = {(1, 0): "ArrowRight", (-1, 0): "ArrowLeft", (0, 1): "ArrowDown", (0, -1): "ArrowUp"}


async def main():
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(
            executable_path="/home/hatch/.cache/ms-playwright/chromium-1255/chrome-linux64/chrome"
        )
        ctx = await browser.new_context(
            viewport={"width": 800, "height": 900},
            record_video_dir=str(OUT),
            record_video_size={"width": 800, "height": 900},
        )
        page = await ctx.new_page()
        await page.goto(GAME)
        await page.wait_for_timeout(600)
        # start the game
        await page.keyboard.press("ArrowRight")
        end = asyncio.get_event_loop().time() + 12.0
        last_score = -1
        while asyncio.get_event_loop().time() < end:
            st = await page.evaluate(
                "() => ({snake: window.__game.snake, food: window.__game.food,"
                " score: window.__game.score, alive: window.__game.alive,"
                " dir: window.__game.dir})"
            )
            if not st["alive"]:
                print("died, score", st["score"], "— restarting", flush=True)
                await page.keyboard.press("r")
                await page.wait_for_timeout(300)
                await page.keyboard.press("ArrowRight")
                continue
            if st["score"] != last_score:
                print("score:", st["score"], flush=True)
                last_score = st["score"]
            head = st["snake"][0]
            food = st["food"]
            dx, dy = st["dir"]["x"], st["dir"]["y"]
            # greedy: move along the axis with the bigger gap, never reverse
            options = []
            if food["x"] > head["x"]:
                options.append((1, 0))
            elif food["x"] < head["x"]:
                options.append((-1, 0))
            if food["y"] > head["y"]:
                options.append((0, 1))
            elif food["y"] < head["y"]:
                options.append((0, -1))
            # pick the first option that is not a reversal; prefer horizontal
            chosen = None
            for opt in options:
                if opt != (-dx, -dy):
                    chosen = opt
                    break
            if chosen is None:
                # head is on the food column/row: keep going straight
                chosen = (dx, dy)
            # avoid running into the body: if the next cell is occupied, turn
            nx, ny = head["x"] + chosen[0], head["y"] + chosen[1]
            body = {(s["x"], s["y"]) for s in st["snake"][:-1]}
            if (nx, ny) in body or not (0 <= nx < 20 and 0 <= ny < 20):
                for alt in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                    if alt == (-dx, -dy):
                        continue
                    ax, ay = head["x"] + alt[0], head["y"] + alt[1]
                    if (ax, ay) not in body and 0 <= ax < 20 and 0 <= ay < 20:
                        chosen = alt
                        break
            await page.keyboard.press(KEYS[chosen])
            await page.wait_for_timeout(140)
        final = await page.evaluate("() => window.__game.score")
        print("final score:", final, flush=True)
        await ctx.close()
        await browser.close()


asyncio.run(main())
