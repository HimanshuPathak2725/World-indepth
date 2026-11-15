"""Optional MapAnything adapter with strict output validation.

This module deliberately imports MapAnything only inside ``run`` so the
single-view baseline and dataset tooling remain usable without its heavyweight
GPU environment.
"""

from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path
from typing import Any

import numpy as np

MODEL_ID = "facebook/map-anything-apache"
MODEL_REVISION = "00f9c245bbcb60522d1ed7f9e9d88462c6e3f38a"
EXPECTED_KEYS = ("pts3d", "pts3d_cam", "intrinsics", "camera_poses", "conf", "mask")


class PredictionError(ValueError):
    """MapAnything returned an incomplete or unsafe prediction."""


def validate_prediction(prediction: dict[str, Any]) -> None:
    missing = {"pts3d", "conf", "mask"} - prediction.keys()
    if missing:
        raise PredictionError(f"prediction missing required keys: {sorted(missing)}")
    points = np.asarray(prediction["pts3d"])
    confidence = np.asarray(prediction["conf"])
    mask = np.asarray(prediction["mask"]).astype(bool)
    if points.ndim != 4 or points.shape[-1] != 3:
        raise PredictionError(f"pts3d must have shape (B,H,W,3), got {points.shape}")
    if confidence.shape[:3] != points.shape[:3] or mask.shape[:3] != points.shape[:3]:
        raise PredictionError("confidence and mask must align with pts3d")
    if not np.isfinite(points).all():
        raise PredictionError("pts3d contains non-finite values")
    if not np.isfinite(confidence).all():
        raise PredictionError("confidence contains non-finite values")
    if np.any(confidence < 0):
        raise PredictionError("confidence contains negative values")


def prediction_summary(predictions: list[dict[str, Any]]) -> dict[str, Any]:
    if not predictions:
        raise PredictionError("model returned no predictions")
    for prediction in predictions:
        validate_prediction(prediction)
    valid = sum(int(np.asarray(prediction["mask"]).astype(bool).sum()) for prediction in predictions)
    confidence = np.concatenate([
        np.asarray(prediction["conf"])[np.asarray(prediction["mask"]).astype(bool)]
        for prediction in predictions
    ])
    return {
        "view_count": len(predictions),
        "valid_point_count": valid,
        "confidence": {
            "count": int(confidence.size),
            "min": float(confidence.min()) if confidence.size else None,
            "mean": float(confidence.mean()) if confidence.size else None,
            "max": float(confidence.max()) if confidence.size else None,
        },
        "keys": sorted(set().union(*(prediction.keys() for prediction in predictions))),
    }


def run(image_paths: list[str], output: str | Path, device: str = "cuda") -> dict[str, Any]:
    """Run the pinned Apache checkpoint; requires a separately provisioned environment."""

    try:
        import torch
        from mapanything.models import MapAnything
        from mapanything.utils.image import load_images
    except ImportError as error:
        raise RuntimeError(
            "MapAnything is not installed; use the documented GPU environment and "
            "install its pinned upstream package before running this adapter"
        ) from error
    if device == "cuda" and not torch.cuda.is_available():
        raise RuntimeError("CUDA device requested but torch.cuda.is_available() is false")
    model = MapAnything.from_pretrained(MODEL_ID).to(device)
    views = load_images(image_paths)
    start = time.perf_counter()
    predictions = model.infer(
        views,
        memory_efficient_inference=True,
        minibatch_size=1,
        use_amp=device == "cuda",
        amp_dtype="bf16",
        apply_mask=True,
        mask_edges=True,
        apply_confidence_mask=False,
        use_multiview_confidence=True,
    )
    elapsed = time.perf_counter() - start
    summary = prediction_summary(predictions)
    output_path = Path(output)
    output_path.mkdir(parents=True, exist_ok=True)
    metadata = {
        "model": MODEL_ID,
        "model_revision": MODEL_REVISION,
        "model_license": "Apache-2.0",
        "device": device,
        "input_image_paths": image_paths,
        "input_sha256": [
            hashlib.sha256(Path(path).read_bytes()).hexdigest() for path in image_paths
        ],
        "inference_seconds": elapsed,
        "prediction_summary": summary,
        "persisted_arrays": ["predictions.npz:view_*_pts3d"],
        "available_outputs_not_persisted": [
            key for key in EXPECTED_KEYS if key not in {"pts3d"}
        ],
        "coordinate_convention": "OpenCV +X right, +Y down, +Z forward; camera-to-world poses",
        "novel_view_metrics": None,
        "novel_view_metrics_note": "Not computed without independently registered held-out cameras and a renderer.",
    }
    (output_path / "metadata.json").write_text(json.dumps(metadata, indent=2) + "\n")
    np.savez_compressed(
        output_path / "predictions.npz",
        **{
            f"view_{index}_pts3d": np.asarray(prediction["pts3d"])
            for index, prediction in enumerate(predictions)
        },
    )
    return metadata
