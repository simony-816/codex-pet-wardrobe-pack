#!/usr/bin/env python3
"""Build and validate Codex pet sprite atlases."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


CELL_W = 192
CELL_H = 208
COLS = 8
ROWS = [
    ("idle", 6),
    ("running-right", 8),
    ("running-left", 8),
    ("waving", 4),
    ("jumping", 5),
    ("failed", 8),
    ("waiting", 6),
    ("running", 6),
    ("review", 6),
]
ATLAS_W = CELL_W * COLS
ATLAS_H = CELL_H * len(ROWS)


def ensure_rgba(path: Path) -> Image.Image:
    return Image.open(path).convert("RGBA")


def compose_atlas(frames_root: Path, output_png: Path, output_webp: Path | None) -> dict:
    atlas = Image.new("RGBA", (ATLAS_W, ATLAS_H), (0, 0, 0, 0))
    cells = []

    for row, (state, count) in enumerate(ROWS):
        for col in range(COLS):
            used = col < count
            if used:
                frame_path = frames_root / state / f"{col:02d}.png"
                if not frame_path.exists():
                    raise FileNotFoundError(frame_path)
                frame = ensure_rgba(frame_path)
                if frame.size != (CELL_W, CELL_H):
                    raise ValueError(f"{frame_path} is {frame.size}, expected {(CELL_W, CELL_H)}")
                atlas.alpha_composite(frame, (col * CELL_W, row * CELL_H))
                nontransparent = sum(1 for p in frame.getdata() if p[3] > 0)
            else:
                nontransparent = 0
            cells.append({"state": state, "row": row, "column": col, "used": used, "nontransparent_pixels": nontransparent})

    output_png.parent.mkdir(parents=True, exist_ok=True)
    atlas.save(output_png)
    if output_webp is not None:
        output_webp.parent.mkdir(parents=True, exist_ok=True)
        atlas.save(output_webp, "WEBP", lossless=True, quality=100, method=6)

    return {"ok": True, "png": str(output_png), "webp": str(output_webp) if output_webp else None, "cells": cells}


def validate_atlas(path: Path) -> dict:
    image = ensure_rgba(path)
    errors = []
    warnings = []
    cells = []

    if image.size != (ATLAS_W, ATLAS_H):
        errors.append(f"atlas is {image.size}, expected {(ATLAS_W, ATLAS_H)}")

    if image.size == (ATLAS_W, ATLAS_H):
        for row, (state, count) in enumerate(ROWS):
            for col in range(COLS):
                cell = image.crop((col * CELL_W, row * CELL_H, (col + 1) * CELL_W, (row + 1) * CELL_H))
                nontransparent = sum(1 for p in cell.getdata() if p[3] > 0)
                used = col < count
                if used and nontransparent == 0:
                    errors.append(f"{state} frame {col:02d} is empty")
                if not used and nontransparent != 0:
                    errors.append(f"{state} unused cell {col:02d} is not transparent")
                cells.append({"state": state, "row": row, "column": col, "used": used, "nontransparent_pixels": nontransparent})

    return {
        "ok": not errors,
        "file": str(path),
        "format": Image.open(path).format,
        "mode": image.mode,
        "width": image.width,
        "height": image.height,
        "errors": errors,
        "warnings": warnings,
        "cells": cells,
    }


def contact_sheet(atlas_path: Path, output: Path) -> dict:
    atlas = ensure_rgba(atlas_path)
    scale = 0.55
    thumb_w = int(CELL_W * scale)
    thumb_h = int(CELL_H * scale)
    label_h = 22
    gutter = 10
    left_label = 118
    sheet_w = left_label + COLS * (thumb_w + gutter) + gutter
    sheet_h = len(ROWS) * (thumb_h + label_h + gutter) + gutter

    sheet = Image.new("RGBA", (sheet_w, sheet_h), (250, 250, 248, 255))
    draw = ImageDraw.Draw(sheet)
    font = ImageFont.load_default()

    for row, (state, count) in enumerate(ROWS):
        y = gutter + row * (thumb_h + label_h + gutter)
        draw.text((gutter, y + 34), f"{row}: {state}", fill=(40, 44, 52), font=font)
        for col in range(COLS):
            x = left_label + col * (thumb_w + gutter)
            draw.rectangle((x, y, x + thumb_w, y + thumb_h), fill=(236, 236, 232), outline=(210, 210, 204))
            if col < count:
                frame = atlas.crop((col * CELL_W, row * CELL_H, (col + 1) * CELL_W, (row + 1) * CELL_H))
                frame = frame.resize((thumb_w, thumb_h), Image.Resampling.LANCZOS)
                sheet.alpha_composite(frame, (x, y))
            draw.text((x + 3, y + thumb_h + 3), f"{col:02d}", fill=(80, 80, 76), font=font)

    output.parent.mkdir(parents=True, exist_ok=True)
    sheet.convert("RGB").save(output)
    return {"ok": True, "file": str(output), "width": sheet_w, "height": sheet_h}


def write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")


def main() -> None:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)

    compose = sub.add_parser("compose")
    compose.add_argument("--frames-root", required=True, type=Path)
    compose.add_argument("--png", required=True, type=Path)
    compose.add_argument("--webp", type=Path)
    compose.add_argument("--report", type=Path)

    validate = sub.add_parser("validate")
    validate.add_argument("--atlas", required=True, type=Path)
    validate.add_argument("--report", type=Path)

    contact = sub.add_parser("contact-sheet")
    contact.add_argument("--atlas", required=True, type=Path)
    contact.add_argument("--output", required=True, type=Path)
    contact.add_argument("--report", type=Path)

    args = parser.parse_args()

    if args.command == "compose":
        result = compose_atlas(args.frames_root, args.png, args.webp)
    elif args.command == "validate":
        result = validate_atlas(args.atlas)
    elif args.command == "contact-sheet":
        result = contact_sheet(args.atlas, args.output)
    else:
        raise AssertionError(args.command)

    if getattr(args, "report", None):
        write_json(args.report, result)
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
