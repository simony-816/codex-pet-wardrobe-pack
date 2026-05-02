#!/usr/bin/env python3
"""Validate the public Codex pet pack before install or publish."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path, PurePosixPath

from PIL import Image

from pet_assets import validate_atlas


MAX_SPRITESHEET_BYTES = 10 * 1024 * 1024
ALLOWED_PET_FILES = {"pet.json", "spritesheet.webp", "spritesheet.png", "validation.json"}
REQUIRED_PET_KEYS = {"id", "displayName", "description", "spritesheetPath"}


def read_json(path: Path) -> dict:
    try:
        data = json.loads(path.read_text())
    except json.JSONDecodeError as exc:
        raise ValueError(f"{path}: invalid JSON: {exc}") from exc
    if not isinstance(data, dict):
        raise ValueError(f"{path}: expected a JSON object")
    return data


def is_safe_local_asset_path(value: str) -> bool:
    if not value or value.strip() != value:
        return False
    if any(ord(ch) < 32 for ch in value):
        return False
    if "://" in value or value.startswith("/") or value.startswith("\\"):
        return False
    parts = PurePosixPath(value.replace("\\", "/")).parts
    if len(parts) != 1:
        return False
    return parts[0] not in {"", ".", ".."} and parts[0].endswith(".webp")


def validate_pet_folder(folder: Path) -> dict:
    errors: list[str] = []
    warnings: list[str] = []
    files = {path.name for path in folder.iterdir() if path.is_file()}

    unexpected = sorted(files - ALLOWED_PET_FILES)
    if unexpected:
        warnings.append(f"unexpected files: {', '.join(unexpected)}")

    pet_json_path = folder / "pet.json"
    if not pet_json_path.exists():
        return {"folder": folder.name, "ok": False, "errors": ["missing pet.json"], "warnings": warnings}

    try:
        metadata = read_json(pet_json_path)
    except ValueError as exc:
        return {"folder": folder.name, "ok": False, "errors": [str(exc)], "warnings": warnings}

    keys = set(metadata)
    missing = sorted(REQUIRED_PET_KEYS - keys)
    if missing:
        errors.append(f"missing pet.json keys: {', '.join(missing)}")

    extra = sorted(keys - REQUIRED_PET_KEYS)
    if extra:
        warnings.append(f"ignored pet.json keys: {', '.join(extra)}")

    pet_id = metadata.get("id")
    if pet_id != folder.name:
        errors.append(f"pet id must match folder name: {pet_id!r} != {folder.name!r}")

    for key in ("displayName", "description"):
        value = metadata.get(key)
        if not isinstance(value, str) or not value.strip():
            errors.append(f"{key} must be a non-empty string")

    spritesheet_path = metadata.get("spritesheetPath")
    if not isinstance(spritesheet_path, str) or not is_safe_local_asset_path(spritesheet_path):
        errors.append("spritesheetPath must be a local .webp file name with no path traversal, URL, or absolute path")
        spritesheet = None
    else:
        spritesheet = folder / spritesheet_path
        if not spritesheet.exists():
            errors.append(f"spritesheet is missing: {spritesheet_path}")
        elif spritesheet.stat().st_size > MAX_SPRITESHEET_BYTES:
            errors.append(f"spritesheet is too large: {spritesheet.stat().st_size} bytes")

    atlas_report = None
    if spritesheet is not None and spritesheet.exists():
        atlas_report = validate_atlas(spritesheet)
        if not atlas_report["ok"]:
            errors.extend(atlas_report["errors"])

    png = folder / "spritesheet.png"
    if png.exists():
        with Image.open(png) as image:
            if image.size != (1536, 1872):
                errors.append(f"spritesheet.png is {image.size}, expected (1536, 1872)")

    return {
        "folder": folder.name,
        "id": pet_id,
        "displayName": metadata.get("displayName"),
        "ok": not errors,
        "errors": errors,
        "warnings": warnings,
        "atlas": atlas_report,
    }


def validate_pack(repo_root: Path) -> dict:
    pets_root = repo_root / "pets"
    manifest_path = pets_root / "manifest.json"
    manifest = read_json(manifest_path)
    manifest_pets = manifest.get("pets")
    if not isinstance(manifest_pets, list):
        raise ValueError(f"{manifest_path}: pets must be a list")

    folders = sorted(path for path in pets_root.iterdir() if path.is_dir())
    pet_reports = [validate_pet_folder(folder) for folder in folders]
    folder_names = [folder.name for folder in folders]
    ids = [report.get("id") for report in pet_reports]

    errors: list[str] = []
    warnings: list[str] = []

    if len(ids) != len(set(ids)):
        errors.append("duplicate pet ids detected")

    manifest_folders = [entry.get("folder") for entry in manifest_pets if isinstance(entry, dict)]
    if manifest_folders != folder_names:
        errors.append(f"manifest folders {manifest_folders!r} do not match pet folders {folder_names!r}")

    for entry in manifest_pets:
        if not isinstance(entry, dict):
            errors.append("manifest contains a non-object pet entry")
            continue
        folder = entry.get("folder")
        matching = next((report for report in pet_reports if report["folder"] == folder), None)
        if matching is None:
            errors.append(f"manifest references missing folder: {folder!r}")
            continue
        for key in ("id", "displayName", "spritesheetPath"):
            expected = read_json(pets_root / folder / "pet.json").get(key)
            if entry.get(key) != expected:
                errors.append(f"manifest {folder}.{key} does not match pet.json")

    for report in pet_reports:
        if not report["ok"]:
            errors.extend(f"{report['folder']}: {error}" for error in report["errors"])
        warnings.extend(f"{report['folder']}: {warning}" for warning in report["warnings"])

    return {
        "ok": not errors,
        "petCount": len(pet_reports),
        "petFolders": folder_names,
        "errors": errors,
        "warnings": warnings,
        "pets": pet_reports,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--report", type=Path)
    parser.add_argument("--summary", action="store_true")
    args = parser.parse_args()

    report = validate_pack(args.repo_root)
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n")
    output = {
        "ok": report["ok"],
        "petCount": report["petCount"],
        "petFolders": report["petFolders"],
        "errors": report["errors"],
        "warnings": report["warnings"],
    } if args.summary else report
    print(json.dumps(output, indent=2, ensure_ascii=False))
    if not report["ok"]:
        sys.exit(1)


if __name__ == "__main__":
    main()
