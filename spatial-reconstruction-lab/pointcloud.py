"""Small CPU-only RGB-D projection primitives for Experiment A."""

from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Iterable

RGB = tuple[int, int, int]
Point = tuple[int, int, tuple[float, float, float], RGB]


@dataclass(frozen=True)
class Intrinsics:
    width: int
    height: int
    fx: float
    fy: float
    cx: float
    cy: float


@dataclass(frozen=True)
class Pose:
    """Camera-to-world pose represented by a rotation matrix and translation."""

    rotation: tuple[tuple[float, float, float], ...]
    position: tuple[float, float, float]
    coordinate_system: str


def _camera_point(u: int, v: int, depth: float, camera: Intrinsics, system: str) -> tuple[float, float, float]:
    if system == "rdf":
        return ((u - camera.cx) / camera.fx * depth,
                (v - camera.cy) / camera.fy * depth,
                depth)
    if system == "rub":
        return ((u - camera.cx) / camera.fx * depth,
                -(v - camera.cy) / camera.fy * depth,
                -depth)
    raise ValueError(f"unsupported camera coordinate system: {system}")


def unproject(
    depth_rows: Iterable[Iterable[float]],
    camera: Intrinsics,
    pose: Pose,
) -> list[tuple[int, int, tuple[float, float, float]]]:
    """Return finite depth pixels transformed from camera to world coordinates."""

    if pose.coordinate_system not in {"rdf", "rub"}:
        raise ValueError(f"unsupported camera coordinate system: {pose.coordinate_system}")
    rows = [tuple(row) for row in depth_rows]
    if len(rows) != camera.height or any(len(row) != camera.width for row in rows):
        raise ValueError("depth grid does not match camera dimensions")
    result = []
    for v, row in enumerate(rows):
        for u, depth in enumerate(row):
            if not math.isfinite(depth) or depth <= 0:
                continue
            x, y, z = _camera_point(u, v, depth, camera, pose.coordinate_system)
            rotation = pose.rotation
            world = (
                rotation[0][0] * x + rotation[0][1] * y + rotation[0][2] * z + pose.position[0],
                rotation[1][0] * x + rotation[1][1] * y + rotation[1][2] * z + pose.position[1],
                rotation[2][0] * x + rotation[2][1] * y + rotation[2][2] * z + pose.position[2],
            )
            result.append((u, v, world))
    return result


def unproject_rgbd(
    rgb_rows: Iterable[Iterable[RGB]],
    depth_rows: Iterable[Iterable[float]],
    camera: Intrinsics,
    pose: Pose,
) -> list[Point]:
    """Unproject finite depth pixels while preserving their RGB samples."""

    colors = [tuple(row) for row in rgb_rows]
    depths = [tuple(row) for row in depth_rows]
    if len(colors) != camera.height or len(depths) != camera.height:
        raise ValueError("RGB-D grids do not match camera dimensions")
    if any(len(row) != camera.width for row in colors + depths):
        raise ValueError("RGB-D grids do not match camera dimensions")
    projected = unproject(depths, camera, pose)
    return [(u, v, xyz, colors[v][u]) for u, v, xyz in projected]


def reproject(
    points: Iterable[tuple[float, float, float]],
    camera: Intrinsics,
    pose: Pose,
) -> list[tuple[float, float, float]]:
    """Project world points back to image coordinates and optical depth."""

    inverse = _transpose(pose.rotation)
    result = []
    for wx, wy, wz in points:
        translated = (wx - pose.position[0], wy - pose.position[1], wz - pose.position[2])
        x = sum(inverse[0][i] * translated[i] for i in range(3))
        y = sum(inverse[1][i] * translated[i] for i in range(3))
        z = sum(inverse[2][i] * translated[i] for i in range(3))
        if pose.coordinate_system == "rdf":
            depth, image_y = z, y
        elif pose.coordinate_system == "rub":
            depth, image_y = -z, -y
        else:
            raise ValueError(f"unsupported camera coordinate system: {pose.coordinate_system}")
        if depth <= 0 or not math.isfinite(depth):
            result.append((math.nan, math.nan, depth))
            continue
        result.append(((x / depth) * camera.fx + camera.cx,
                       (image_y / depth) * camera.fy + camera.cy,
                       depth))
    return result


def _transpose(matrix: tuple[tuple[float, float, float], ...]) -> tuple[tuple[float, float, float], ...]:
    return tuple(tuple(matrix[row][column] for row in range(3)) for column in range(3))


def write_ply(path: str, points: Iterable[Point]) -> int:
    """Write an ASCII PLY point cloud and return the number of vertices."""

    rows = list(points)
    with open(path, "w", encoding="ascii") as output:
        output.write("ply\nformat ascii 1.0\n")
        output.write(f"element vertex {len(rows)}\n")
        output.write("property float x\nproperty float y\nproperty float z\n")
        output.write("property uchar red\nproperty uchar green\nproperty uchar blue\nend_header\n")
        for _, _, (x, y, z), (red, green, blue) in rows:
            output.write(f"{x:.8g} {y:.8g} {z:.8g} {red} {green} {blue}\n")
    return len(rows)
