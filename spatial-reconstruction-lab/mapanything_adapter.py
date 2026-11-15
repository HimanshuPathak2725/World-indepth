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
SOURCE_REVISION = "3d10cf7a3016fc0f9bb13a071ee66c47b10be0d9"
OUTPUT_KEYS = (
    "pts3d",
    "pts3d_cam",
    "depth_z",
    "depth_along_ray",
    "intrinsics",
    "camera_poses",
    "cam_trans",
    "cam_quats",
    "conf",
    "mask",
)


class PredictionError(ValueError):
    """MapAnything returned an incomplete or unsafe prediction."""


def _array(value: Any) -> np.ndarray:
    if hasattr(value, "detach"):
        value = value.detach().cpu().numpy()
    return np.asarray(value)


def _mask_array(value: Any) -> np.ndarray:
    mask = _array(value).astype(bool)
    return mask[..., 0] if mask.ndim == 4 and mask.shape[-1] == 1 else mask


def validate_prediction(prediction: dict[str, Any]) -> None:
    missing = {"pts3d", "conf", "mask"} - prediction.keys()
    if missing:
        raise PredictionError(f"prediction missing required keys: {sorted(missing)}")
    points = _array(prediction["pts3d"])
    confidence = _array(prediction["conf"])
    mask = _mask_array(prediction["mask"])
    if points.ndim != 4 or points.shape[-1] != 3:
        raise PredictionError(f"pts3d must have shape (B,H,W,3), got {points.shape}")
    if confidence.shape != points.shape[:3] or mask.shape != points.shape[:3]:
        raise PredictionError("confidence and mask must align with pts3d")
    if not np.isfinite(points).all():
        raise PredictionError("pts3d contains non-finite values")
    if not np.isfinite(confidence).all():
        raise PredictionError("confidence contains non-finite values")
    if np.any(confidence < 0):
        raise PredictionError("confidence contains negative values")


def validate_complete_prediction(prediction: dict[str, Any]) -> None:
    missing = set(OUTPUT_KEYS) - prediction.keys()
    if missing:
        raise PredictionError(f"complete prediction missing keys: {sorted(missing)}")
    validate_prediction(prediction)
    points = _array(prediction["pts3d"])
    expected_shapes = {
        "pts3d_cam": points.shape,
        "depth_z": (*points.shape[:3], 1),
        "depth_along_ray": (*points.shape[:3], 1),
        "intrinsics": (points.shape[0], 3, 3),
        "camera_poses": (points.shape[0], 4, 4),
        "cam_trans": (points.shape[0], 3),
        "cam_quats": (points.shape[0], 4),
    }
    for key, shape in expected_shapes.items():
        value = _array(prediction[key])
        if value.shape != shape:
            raise PredictionError(f"{key} must have shape {shape}, got {value.shape}")
        if not np.isfinite(value).all():
            raise PredictionError(f"{key} contains non-finite values")


def prediction_summary(predictions: list[dict[str, Any]]) -> dict[str, Any]:
    if not predictions:
        raise PredictionError("model returned no predictions")
    for prediction in predictions:
        validate_prediction(prediction)
    valid = sum(int(_mask_array(prediction["mask"]).sum()) for prediction in predictions)
    confidence = np.concatenate([
        _array(prediction["conf"])[_mask_array(prediction["mask"])]
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


def save_predictions(predictions: list[dict[str, Any]], output: str | Path) -> list[str]:
    """Persist every documented output that the model returned, as CPU NumPy arrays."""

    arrays: dict[str, np.ndarray] = {}
    for view_index, prediction in enumerate(predictions):
        validate_complete_prediction(prediction)
        for key in OUTPUT_KEYS:
            if key in prediction:
                arrays[f"view_{view_index}_{key}"] = _array(prediction[key])
    output_path = Path(output)
    output_path.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(output_path / "predictions.npz", **arrays)
    return sorted(arrays)


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
    model = MapAnything.from_pretrained(MODEL_ID, revision=MODEL_REVISION).to(device)
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
        "source_revision": SOURCE_REVISION,
        "model_license": "Apache-2.0",
        "device": device,
        "input_image_paths": image_paths,
        "input_sha256": [
            hashlib.sha256(Path(path).read_bytes()).hexdigest() for path in image_paths
        ],
        "inference_seconds": elapsed,
        "prediction_summary": summary,
        "persisted_arrays": [],
        "coordinate_convention": "OpenCV +X right, +Y down, +Z forward; camera-to-world poses",
        "novel_view_metrics": None,
        "novel_view_metrics_note": "Not computed without independently registered held-out cameras and a renderer.",
    }
    metadata["persisted_arrays"] = save_predictions(predictions, output)
    (output_path / "metadata.json").write_text(json.dumps(metadata, indent=2) + "\n")
    return metadata
