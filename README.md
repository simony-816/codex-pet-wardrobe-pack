# Codex Pet Wardrobe Pack

Custom chibi pet sprite for the Codex desktop app.

This repository is prepared as a neutral public-sharing package. It intentionally avoids official character names, series names, logos, screenshots, and reference captures in package IDs and distributed assets.

## Pets

| Pet | Folder | Preview | Notes |
| --- | --- | --- | --- |
| Thorny Daily v1 | `pets/thorny-daily-v1` | `previews/thorny-daily-v1-contact-sheet.png` | Original cozy daily-outfit version. |
| Thorny Shadow v1 | `pets/thorny-shadow-v1` | `previews/thorny-shadow-v1-contact-sheet.png` | Dark action-outfit version with combat-style work, review, and mishap motions. |

## Preview

![Thorny Daily v1 contact sheet](previews/thorny-daily-v1-contact-sheet.png)

![Thorny Shadow v1 contact sheet](previews/thorny-shadow-v1-contact-sheet.png)

## Install

Copy both pet folders into your Codex pets directory:

```sh
mkdir -p ~/.codex/pets
cp -R pets/thorny-daily-v1 pets/thorny-shadow-v1 ~/.codex/pets/
```

Then open Codex settings and choose either custom pet from Appearance > Pets.

If the pet list or sprite appears stale, use Refresh in the pets settings, then tuck away and wake the pet.

## Sprite Format

Each pet folder contains:

```text
pet.json
spritesheet.webp
spritesheet.png
```

Codex currently expects a `1536 x 1872` sprite atlas:

- 8 columns x 9 rows
- each cell is `192 x 208`
- transparent unused cells
- `spritesheet.webp` referenced from `pet.json`

See [docs/SPRITE_SPEC.md](docs/SPRITE_SPEC.md) for the row mapping.

## Validate

```sh
python3 scripts/check_pack.py
python3 scripts/pet_assets.py validate --atlas pets/thorny-daily-v1/spritesheet.webp
python3 scripts/pet_assets.py validate --atlas pets/thorny-shadow-v1/spritesheet.webp
```

`scripts/check_pack.py` verifies that every pet folder has a safe local `spritesheetPath`, unique IDs, manifest consistency, and a valid Codex atlas.

## Changelog

- 2026-05-02: Added `thorny-shadow-v1`, a dark action-outfit variant. The public pack now contains two installable Codex pets.
- 2026-05-02: Added `scripts/check_pack.py` to validate clone/install readiness and guard against unsafe pet metadata paths.
- 2026-05-02: Published the initial `thorny-daily-v1` cozy daily-outfit pet.

## Asset Notice

No open-source license is granted for the artwork assets in this repository. Treat the sprites as personal, non-commercial fan-work assets unless and until the designs are replaced with substantially original characters.

Code in `scripts/` may be reused for personal pet-building workflows.

## Public Sharing Caution

This pack was prepared to reduce public repository risk by using neutral names and excluding official artwork, but fan-made sprites can still raise IP concerns if they are recognizable as a protected character.

Before publishing publicly, read [docs/COPYRIGHT_AND_PUBLIC_SHARING.md](docs/COPYRIGHT_AND_PUBLIC_SHARING.md). A disclaimer does not grant permission from any rights holder.
