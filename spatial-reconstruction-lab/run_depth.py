"""Run Depth Anything V2 Small and build a colored pseudo-depth point cloud."""

from __future__ import annotations

import argparse
import json
import math
import sys
import time
from pathlib import Path

import numpy as np
import torch
from PIL import Image
from transformers import AutoImageProcessor, AutoModelForDepthEstimation

from pointcloud import Intrinsics, Pose, reproject, unproject_rgbd, write_compact


MODEL_ID = "depth-anything/Depth-Anything-V2-Small-hf"
DEFAULT_OUTPUT_FILES = (
    "depth.npy",
    "depth_visualization.png",
    "pointcloud.wipcld",
    "camera.json",
    "metrics.json",
)


def write_pointcloud_output(output: Path, points: list) -> int:
    """Write only the compact public point-cloud artifact."""

    return write_compact(str(output / "pointcloud.wipcld"), points)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--image", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--fov-degrees", type=float, default=80.0)
    args = parser.parse_args()

    args.output.mkdir(parents=True, exist_ok=True)
    image = Image.open(args.image).convert("RGB")
    width, height = image.size
    processor = AutoImageProcessor.from_pretrained(MODEL_ID)
    model = AutoModelForDepthEstimation.from_pretrained(MODEL_ID).eval()

    start = time.perf_counter()
    inputs = processor(images=image, return_tensors="pt")
    with torch.inference_mode():
        predicted = model(**inputs).predicted_depth
    elapsed = time.perf_counter() - start
    prediction = torch.nn.functional.interpolate(
        predicted.unsqueeze(1), size=(height, width), mode="bicubic", align_corners=False
    )[0, 0].cpu().numpy().astype(np.float32)

    finite = np.isfinite(prediction)
    if not finite.any():
        raise RuntimeError("depth model returned no finite values")
    low, high = float(prediction[finite].min()), float(prediction[finite].max())
    normalized_inverse = np.zeros_like(prediction)
    if high > low:
        normalized_inverse[finite] = (prediction[finite] - low) / (high - low)
    # Depth Anything is relative depth, not metres. Higher model values are
    # treated as nearer, so invert the normalized signal into pseudo-depth.
    pseudo_depth = np.full_like(prediction, np.nan)
    pseudo_depth[finite] = 1.0 + (1.0 - normalized_inverse[finite]) * 4.0

    np.save(args.output / "depth.npy", pseudo_depth)
    depth_visual = np.clip(normalized_inverse * 255.0, 0, 255).astype(np.uint8)
    Image.fromarray(depth_visual, mode="L").save(args.output / "depth_visualization.png")

    focal = width / (2.0 * math.tan(math.radians(args.fov_degrees) / 2.0))
    camera = Intrinsics(width, height, focal, focal, (width - 1) / 2.0, (height - 1) / 2.0)
    pose = Pose(((1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0)),
                (0.0, 0.0, 0.0), "rdf")
    rgb = np.asarray(image, dtype=np.uint8)
    points = unproject_rgbd(rgb.tolist(), pseudo_depth.tolist(), camera, pose)
    if not points or any(not all(math.isfinite(value) for value in xyz) for _, _, xyz, _ in points):
        raise RuntimeError("point cloud contains no valid finite points")
    point_count = write_pointcloud_output(args.output, points)
    reprojections = reproject([point[2] for point in points], camera, pose)
    reprojection_error = max(
        math.hypot(u - pixel_u, v - pixel_v)
        for (pixel_u, pixel_v, _, _), (u, v, _) in zip(points, reprojections)
    )
    camera_json = {
        "intrinsics": vars(camera),
        "extrinsics": {
            "position": list(pose.position),
            "rotation_matrix": [list(row) for row in pose.rotation],
            "coordinate_system": pose.coordinate_system,
        },
        "assumptions": {
            "horizontal_fov_degrees": args.fov_degrees,
            "metric_scale": False,
            "depth_units": "arbitrary pseudo-depth units",
        },
    }
    (args.output / "camera.json").write_text(json.dumps(camera_json, indent=2) + "\n", encoding="utf-8")
    metrics = {
        "model": MODEL_ID,
        "model_revision": "5426e4f0f36572d16453bbda7a8389317b1bef99",
        "device": "cpu",
        "inference_seconds": elapsed,
        "input_dimensions": [width, height],
        "output_dimensions": [width, height],
        "raw_prediction_range": [low, high],
        "normalized_inverse_depth_range": [0.0, 1.0],
        "pseudo_depth_range": [float(np.nanmin(pseudo_depth)), float(np.nanmax(pseudo_depth))],
        "invalid_pixel_count": int((~finite).sum()),
        "valid_pixel_count": int(finite.sum()),
        "point_count": point_count,
        "compact_format": "WIPCLD01: little-endian uint32 count; float32 XYZ; uint8 RGB",
        "compact_artifact": "pointcloud.wipcld",
        "reprojection_max_pixel_error": reprojection_error,
        "depth_semantics": "relative/inverse-like model output, explicitly normalized and inverted; not metric",
        "normalization_policy": "finite raw output min-max to [0,1], then pseudo-depth = 1 + (1 - normalized) * 4",
    }
    (args.output / "metrics.json").write_text(json.dumps(metrics, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(metrics, indent=2))


if __name__ == "__main__":
    sys.exit(main())
