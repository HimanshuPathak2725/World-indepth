"""Validation and deterministic view selection for private multi-view scenes."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from PIL import Image

VIEW_BUDGETS = (1, 2, 3, 5, 8)


class DatasetError(ValueError):
    """A dataset manifest or image set is not safe to use."""


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_manifest(path: str | Path) -> dict[str, Any]:
    manifest_path = Path(path)
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise DatasetError(f"cannot read manifest: {error}") from error
    validate_manifest(manifest, manifest_path.parent)
    return manifest


def validate_manifest(manifest: dict[str, Any], root: str | Path) -> None:
    if not isinstance(manifest, dict):
        raise DatasetError("manifest must be an object")
    required = {"schema_version", "scene_id", "origin", "views", "held_out"}
    missing = required - manifest.keys()
    if missing:
        raise DatasetError(f"manifest missing fields: {sorted(missing)}")
    if manifest["schema_version"] != 1 or not manifest["scene_id"]:
        raise DatasetError("schema_version must be 1 and scene_id must be non-empty")
    if not isinstance(manifest["origin"], dict) or not manifest["origin"].get("license"):
        raise DatasetError("origin.license is required and must be explicit")
    views = manifest["views"]
    held_out = manifest["held_out"]
    if not isinstance(views, list) or not isinstance(held_out, list) or not views:
        raise DatasetError("views and held_out must be non-empty lists")
    root_path = Path(root)
    seen_ids: set[str] = set()
    seen_hashes: set[str] = set()
    all_names: set[str] = set()
    for view in views + held_out:
        if not isinstance(view, dict):
            raise DatasetError("each view must be an object")
        for field in ("id", "filename", "sha256", "width", "height"):
            if field not in view:
                raise DatasetError(f"view missing {field}")
        if view["id"] in seen_ids:
            raise DatasetError(f"duplicate view id: {view['id']}")
        if view["filename"] in all_names:
            raise DatasetError(f"duplicate filename: {view['filename']}")
        seen_ids.add(view["id"])
        all_names.add(view["filename"])
        if view["sha256"] in seen_hashes:
            raise DatasetError(f"duplicate image hash: {view['sha256']}")
        seen_hashes.add(view["sha256"])
        image_path = root_path / view["filename"]
        if not image_path.is_file():
            raise DatasetError(f"missing image: {image_path}")
        if _sha256(image_path) != view["sha256"]:
            raise DatasetError(f"sha256 mismatch: {image_path}")
        try:
            with Image.open(image_path) as image:
                dimensions = image.size
                image.verify()
        except Exception as error:
            raise DatasetError(f"unreadable image {image_path}: {error}") from error
        if tuple(dimensions) != (view["width"], view["height"]):
            raise DatasetError(f"dimension mismatch: {image_path}")
    if set(view["id"] for view in views) & set(view["id"] for view in held_out):
        raise DatasetError("a view cannot be both input and held-out")


def select_input_views(manifest: dict[str, Any], budget: int) -> list[dict[str, Any]]:
    """Select the first deterministic capture-order views without held-out leakage."""

    if budget not in VIEW_BUDGETS:
        raise DatasetError(f"budget must be one of {VIEW_BUDGETS}")
    views = manifest["views"]
    if budget > len(views):
        raise DatasetError(f"budget {budget} exceeds {len(views)} input views")
    ordered = sorted(views, key=lambda view: (view.get("capture_order", 0), view["id"]))
    return ordered[:budget]


def validate_budget_inputs(manifest: dict[str, Any], selected_ids: list[str], budget: int) -> None:
    selected = {view["id"] for view in select_input_views(manifest, budget)}
    held_out = {view["id"] for view in manifest["held_out"]}
    if set(selected_ids) != selected or set(selected_ids) & held_out:
        raise DatasetError("selected inputs do not match deterministic budget or leak held-out views")
