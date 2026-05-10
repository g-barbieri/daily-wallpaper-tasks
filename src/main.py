from __future__ import annotations

import argparse
import ctypes
import json
from datetime import date
import math
from pathlib import Path
import re

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parent.parent
CONFIG_FILE = ROOT / "config.json"
OUTPUT_DIR = ROOT / "output"


SECTION_PATTERN = re.compile(r"^\s{0,3}(#{2,4})\s+(.*?)\s*$")
TASK_PATTERN = re.compile(r"^\s*[-*]\s+\[( |x|X)\]\s*(.*)$")


def load_config(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def resolve_daily_note(config: dict) -> Path:
    vault_path = Path(config["vault_path"])
    return vault_path / config.get("source_note", "Today.md")


def load_sections_from_note(
    path: Path,
    fallback_headings: list[str],
    task_markers: list[str],
) -> list[dict[str, object]]:
    if not path.exists():
        return [{"heading": heading, "items": []} for heading in fallback_headings]

    del task_markers

    sections: list[dict[str, object]] = []
    section_lookup: dict[str, dict[str, object]] = {}
    current_section: dict[str, object] | None = None

    for line in path.read_text(encoding="utf-8").splitlines():
        heading_match = SECTION_PATTERN.match(line)
        if heading_match:
            heading_text = heading_match.group(2).strip()
            current_section = section_lookup.get(heading_text.lower())
            if current_section is None:
                current_section = {"heading": heading_text, "items": []}
                section_lookup[heading_text.lower()] = current_section
                sections.append(current_section)
            continue

        if current_section is None:
            continue

        task_match = TASK_PATTERN.match(line)
        if not task_match:
            continue

        task_text = task_match.group(2).strip()
        if not task_text:
            continue

        items = current_section["items"]
        assert isinstance(items, list)
        items.append(
            {
                "text": task_text,
                "checked": task_match.group(1).lower() == "x",
            }
        )

    if not sections:
        return [{"heading": heading, "items": []} for heading in fallback_headings]

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


def section_grid(section_count: int) -> tuple[int, int]:
    if section_count <= 1:
        return 1, 1
    if section_count <= 4:
        return 2, math.ceil(section_count / 2)
    return 3, math.ceil(section_count / 3)


def first_open_task(sections: list[dict[str, object]]) -> str:
    for section in sections:
        items = section["items"]
        assert isinstance(items, list)
        for item in items:
            if not bool(item["checked"]):
                return str(item["text"])
    return "Write the most important thing first."


def build_wallpaper(sections: list[dict[str, object]], output_path: Path) -> Path:
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

    columns, rows = section_grid(max(len(sections), 1))
    gap_x = 30
    gap_y = 30
    start_x = 90
    start_y = 270
    footer_y = 1000
    card_width = (width - (start_x * 2) - gap_x * (columns - 1)) // columns
    card_height = (footer_y - start_y - gap_y * (rows - 1)) // rows
    accent_colors = [accent2, accent3, accent, "#fb7185", "#34d399", "#f97316"]

    for index, section in enumerate(sections):
        row = index // columns
        column = index % columns
        left = start_x + column * (card_width + gap_x)
        top = start_y + row * (card_height + gap_y)
        right = left + card_width
        bottom = top + card_height

        draw_round_box(draw, (left, top, right, bottom), panel_soft, 28)

        heading_text = str(section["heading"])
        items = section["items"]
        assert isinstance(items, list)
        color = accent_colors[index % len(accent_colors)]
        draw.text((left + 28, top + 24), heading_text, fill=color, font=section_font)
        draw.line((left + 28, top + 74, right - 28, top + 74), fill="#25344f", width=2)

        if not items:
            draw.text((left + 30, top + 110), "Nothing listed.", fill=muted, font=body_font)
            continue

        y = top + 110
        for item in items[:8]:
            task_text = str(item["text"])
            task_lines = wrap_text(draw, task_text, body_font, right - left - 90)
            checked = bool(item["checked"])
            checkbox = "☑" if checked else "☐"
            line_height = 36
            draw.text((left + 30, y), checkbox, fill=color if not checked else muted, font=section_font)
            text_y = y + 3
            for line in task_lines[:3]:
                draw.text((left + 74, text_y), line, fill=foreground if not checked else muted, font=body_font)
                text_y += line_height
            y = text_y + 18
            if y > bottom - 70:
                break

    draw.text(
        (90, 1000),
        "Keep the note focused: one line per task, grouped into the sections you actually use.",
        fill=muted,
        font=small_font,
    )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    image.save(output_path)
    return output_path


def build_companion_wallpaper(sections: list[dict[str, object]], output_path: Path) -> Path:
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
    for section in sections:
        items = section["items"]
        assert isinstance(items, list)
        summary_lines.append(f"{section['heading']}: {len(items)}")

    y = 320
    for line in summary_lines:
        draw.text((140, y), line, fill=foreground, font=body_font)
        y += 70

    draw_round_box(draw, (120, 600, width - 120, 860), "#0b1423", 32)
    draw.text((160, 650), "One sentence for the day", fill=muted, font=small_font)
    draw.text((160, 700), first_open_task(sections), fill=foreground, font=body_font)

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
        config.get("note_headings", ["Priorities", "Errands", "Today"]),
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
