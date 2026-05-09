from __future__ import annotations

import argparse
import ctypes
import json
from datetime import date
from pathlib import Path
import re

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parent.parent
CONFIG_FILE = ROOT / "config.json"
OUTPUT_DIR = ROOT / "output"


def load_config(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def resolve_daily_note(config: dict) -> Path:
    vault_path = Path(config["vault_path"])
    return vault_path / config.get("source_note", "Today.md")


def load_sections_from_note(path: Path, headings: list[str], task_markers: list[str]) -> dict[str, list[dict[str, str]]]:
    if not path.exists():
        return {heading: [] for heading in headings}

    lines = path.read_text(encoding="utf-8").splitlines()
    heading_map = {heading.lower(): heading for heading in headings}
    heading_matchers = {
        heading.lower(): re.compile(rf"^\s*{re.escape(heading)}\s*$", re.IGNORECASE)
        for heading in headings
    }
    sections: dict[str, list[dict[str, str]]] = {heading: [] for heading in headings}
    current_heading: str | None = None

    for line in lines:
        matched_heading = None
        for key, matcher in heading_matchers.items():
            if matcher.match(line):
                matched_heading = heading_map[key]
                break

        if matched_heading is not None:
            current_heading = matched_heading
            continue

        if current_heading and line.startswith("#"):
            current_heading = None
            continue

        if current_heading:
            stripped = line.strip()
            for marker in task_markers:
                if stripped.startswith(marker):
                    task = stripped[len(marker) :].strip()
                    if task:
                        checked = False
                        if task.startswith("[x] "):
                            checked = True
                            task = task[4:].strip()
                        sections[current_heading].append({"text": task, "checked": "true" if checked else "false"})
                    break

    return sections


def load_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = [
        r"C:\Windows\Fonts\segoeuib.ttf" if bold else r"C:\Windows\Fonts\segoeui.ttf",
        r"C:\Windows\Fonts\arialbd.ttf" if bold else r"C:\Windows\Fonts\arial.ttf",
    ]
    for candidate in candidates:
        font_path = Path(candidate)
        if font_path.exists():
            return ImageFont.truetype(str(font_path), size=size)
    return ImageFont.load_default()


def draw_round_box(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], fill: str, radius: int = 28) -> None:
    draw.rounded_rectangle(box, radius=radius, fill=fill)


def wrap_text(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.ImageFont, max_width: int) -> list[str]:
    words = text.split()
    lines: list[str] = []
    current = ""
    for word in words:
        candidate = word if not current else f"{current} {word}"
        if draw.textlength(candidate, font=font) <= max_width:
            current = candidate
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines or [text]


def build_wallpaper(sections: dict[str, list[dict[str, str]]], output_path: Path) -> Path:
    width, height = 1920, 1080
    background = "#08111f"
    panel = "#101b2f"
    panel_soft = "#0d1728"
    foreground = "#f8fafc"
    muted = "#94a3b8"
    accent = "#7dd3fc"
    accent2 = "#fbbf24"
    accent3 = "#a78bfa"

    image = Image.new("RGB", (width, height), background)
    draw = ImageDraw.Draw(image)

    title_font = load_font(60, bold=True)
    date_font = load_font(26)
    section_font = load_font(30, bold=True)
    body_font = load_font(30)
    small_font = load_font(20)

    today = date.today().strftime("%A, %B %d, %Y")
    draw_round_box(draw, (50, 50, width - 50, height - 50), panel, 40)
    draw_round_box(draw, (70, 70, width - 70, 230), panel_soft, 32)
    draw.text((110, 95), "Today", fill=accent, font=title_font)
    draw.text((110, 166), today, fill=muted, font=date_font)
    draw.text((width - 510, 108), "Obsidian dashboard", fill=muted, font=small_font)
    draw.line((110, 222, width - 110, 222), fill="#22304b", width=2)

    columns = [
        ("## Priorities", accent2, (90, 270, 620, 980)),
        ("## Errands", accent3, (650, 270, 1180, 980)),
        ("## Today", accent, (1210, 270, 1830, 980)),
    ]

    for heading, color, box in columns:
        left, top, right, bottom = box
        draw_round_box(draw, box, panel_soft, 28)
        draw.text((left + 28, top + 24), heading.removeprefix("## ").strip(), fill=color, font=section_font)
        draw.line((left + 28, top + 74, right - 28, top + 74), fill="#25344f", width=2)

        items = sections.get(heading, [])
        if not items:
            draw.text((left + 30, top + 110), "Nothing listed.", fill=muted, font=body_font)
            continue

        y = top + 110
        for item in items[:6]:
            text = item["text"]
            lines = wrap_text(draw, text, body_font, right - left - 90)
            checkbox = "☑" if item["checked"] == "true" else "☐"
            line_height = 36
            draw.text((left + 30, y), checkbox, fill=color if item["checked"] == "false" else muted, font=section_font)
            text_y = y + 3
            for line in lines[:3]:
                draw.text((left + 74, text_y), line, fill=foreground if item["checked"] == "false" else muted, font=body_font)
                text_y += line_height
            y = text_y + 18
            if y > bottom - 70:
                break

    draw.text((90, 1000), "Keep the note focused: one line per task, grouped under Priorities, Errands, and Today.", fill=muted, font=small_font)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    image.save(output_path)
    return output_path


def build_companion_wallpaper(sections: dict[str, list[dict[str, str]]], output_path: Path) -> Path:
    width, height = 1920, 1080
    background = "#09101d"
    panel = "#0f1727"
    foreground = "#f8fafc"
    muted = "#94a3b8"
    accent = "#7dd3fc"

    image = Image.new("RGB", (width, height), background)
    draw = ImageDraw.Draw(image)

    title_font = load_font(54, bold=True)
    body_font = load_font(28)
    small_font = load_font(20)

    draw_round_box(draw, (70, 70, width - 70, height - 70), panel, 44)
    draw.text((120, 120), "Focus", fill=accent, font=title_font)
    draw.text((120, 190), "Keep the main screen busy. Keep this one calm.", fill=muted, font=small_font)

    summary_lines = []
    for heading in ("## Priorities", "## Errands", "## Today"):
        total = len(sections.get(heading, []))
        summary_lines.append(f"{heading.removeprefix('## ').strip()}: {total}")

    y = 320
    for line in summary_lines:
        draw.text((140, y), line, fill=foreground, font=body_font)
        y += 70

    draw_round_box(draw, (120, 600, width - 120, 860), "#0b1423", 32)
    draw.text((160, 650), "One sentence for the day", fill=muted, font=small_font)
    top_priority = sections.get("## Priorities", [])[:1]
    if top_priority:
        text = top_priority[0]["text"]
    else:
        text = "Write the most important thing first."
    draw.text((160, 700), text, fill=foreground, font=body_font)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    image.save(output_path)
    return output_path


def set_wallpaper(path: Path) -> None:
    SPI_SETDESKWALLPAPER = 20
    ctypes.windll.user32.SystemParametersInfoW(
        SPI_SETDESKWALLPAPER,
        0,
        str(path),
        3,
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--set-wallpaper", action="store_true")
    parser.add_argument("--note-path", type=str, default=None)
    args = parser.parse_args()

    config = load_config(CONFIG_FILE)
    note_path = Path(args.note_path) if args.note_path else resolve_daily_note(config)
    sections = load_sections_from_note(
        note_path,
        config.get("note_headings", ["## Priorities", "## Errands", "## Today"]),
        list(config.get("task_markers", ["- [ ]", "* [ ]"])),
    )
    primary_path = OUTPUT_DIR / "today-main.png"
    companion_path = OUTPUT_DIR / "today-companion.png"
    build_wallpaper(sections, primary_path)
    build_companion_wallpaper(sections, companion_path)

    if args.set_wallpaper:
        set_wallpaper(primary_path)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
