# Multi-view capture contract

The View Budget Challenge uses one static scene with overlapping images. A
future capture should contain at least 12 RGB photographs: up to eight input
views and at least four held-out views. Keep objects, lighting, focus, and
exposure stable; move the camera rather than the scene.

## Private directory layout

```text
private/scenes/<scene-id>/
  manifest.json
  images/
    view-001.jpg
  outputs/                 # ignored generated results
```

`private/` is ignored by default. Never commit personal photographs, EXIF
location data, model weights, or generated scene outputs without an explicit
licence decision.

## Manifest

The manifest is JSON with `schema_version: 1`, a scene ID, explicit origin and
licence, `views`, and `held_out`. Each image record contains an ID, relative
filename, SHA-256, capture order, width, and height. Optional camera metadata
may include intrinsics, pose, and EXIF, but unknown values must be omitted
rather than guessed.

Validate a manifest with:

```sh
python validate_dataset.py private/scenes/<scene-id>/manifest.json
```

The validator rejects missing or unreadable files, duplicate IDs, duplicate
hashes, dimension mismatches, malformed manifests, and held-out leakage.
Budgets are deterministic prefixes of capture order: `1, 2, 3, 5, 8`.

No multi-view scene has been captured or reconstructed yet; this contract does
not fabricate results.
