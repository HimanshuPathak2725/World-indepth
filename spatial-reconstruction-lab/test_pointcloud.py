import math
import unittest

from pointcloud import (
    Intrinsics,
    Pose,
    read_compact,
    reproject,
    unproject,
    unproject_rgbd,
    write_compact,
    write_ply,
)
from run_depth import DEFAULT_OUTPUT_FILES, write_pointcloud_output


IDENTITY = ((1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0))


class PointCloudTests(unittest.TestCase):
    def test_rdf_uses_optical_axis_depth_and_camera_to_world_translation(self):
        camera = Intrinsics(3, 2, 1.0, 1.0, 1.0, 0.5)
        pose = Pose(IDENTITY, (10.0, 20.0, 30.0), "rdf")
        points = unproject(((2.0, 2.0, 2.0), (2.0, math.nan, 2.0)), camera, pose)
        self.assertEqual(points[0], (0, 0, (8.0, 19.0, 32.0)))
        self.assertEqual(len(points), 5)

    def test_rub_flips_vertical_and_forward_axes(self):
        camera = Intrinsics(1, 1, 2.0, 2.0, 0.0, 0.0)
        pose = Pose(IDENTITY, (0.0, 0.0, 0.0), "rub")
        self.assertEqual(unproject(((4.0,),), camera, pose)[0][2], (0.0, 0.0, -4.0))

    def test_rejects_mismatched_grid(self):
        camera = Intrinsics(2, 1, 1.0, 1.0, 0.0, 0.0)
        with self.assertRaises(ValueError):
            unproject(((1.0,),), camera, Pose(IDENTITY, (0.0, 0.0, 0.0), "rdf"))

    def test_rejects_unknown_coordinate_system(self):
        camera = Intrinsics(1, 1, 1.0, 1.0, 0.0, 0.0)
        with self.assertRaises(ValueError):
            unproject(((1.0,),), camera, Pose(IDENTITY, (0.0, 0.0, 0.0), "unknown"))

    def test_rgbd_preserves_color_alignment(self):
        camera = Intrinsics(2, 1, 1.0, 1.0, 0.0, 0.0)
        points = unproject_rgbd([[(12, 34, 56), (78, 90, 12)]], [[2.0, math.nan]], camera,
                                Pose(IDENTITY, (0.0, 0.0, 0.0), "rdf"))
        self.assertEqual(points, [(0, 0, (0.0, 0.0, 2.0), (12, 34, 56))])

    def test_reprojection_round_trips_rdf(self):
        camera = Intrinsics(3, 2, 2.0, 2.0, 1.0, 0.5)
        pose = Pose(IDENTITY, (4.0, 5.0, 6.0), "rdf")
        points = unproject(((2.0, 2.0, 2.0), (2.0, 2.0, 2.0)), camera, pose)
        reprojections = reproject([point[2] for point in points], camera, pose)
        self.assertEqual([(round(u, 6), round(v, 6), round(z, 6)) for u, v, z in reprojections],
                         [(0.0, 0.0, 2.0), (1.0, 0.0, 2.0), (2.0, 0.0, 2.0),
                          (0.0, 1.0, 2.0), (1.0, 1.0, 2.0), (2.0, 1.0, 2.0)])

    def test_ply_output_has_integrity_header(self):
        import tempfile
        from pathlib import Path

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "points.ply"
            count = write_ply(str(path), [(0, 0, (1.0, 2.0, 3.0), (4, 5, 6))])
            text = path.read_text(encoding="ascii")
            self.assertEqual(count, 1)
            self.assertIn("element vertex 1", text)
            self.assertTrue(text.endswith("1 2 3 4 5 6\n"))

    def test_compact_output_round_trips_points_and_colors(self):
        import tempfile
        from pathlib import Path

        points = [(0, 0, (1.25, -2.5, 3.75), (4, 5, 6))]
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "points.wipcld"
            self.assertEqual(write_compact(str(path), points), 1)
            loaded = read_compact(str(path))
            self.assertEqual(loaded, [((1.25, -2.5, 3.75), (4, 5, 6))])
            self.assertEqual(path.stat().st_size, 8 + 4 + 15)

    def test_compact_reader_rejects_truncated_payload(self):
        import tempfile
        from pathlib import Path

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "bad.wipcld"
            path.write_bytes(b"WIPCLD01" + (2).to_bytes(4, "little") + b"\0" * 15)
            with self.assertRaises(ValueError):
                read_compact(str(path))

    def test_baseline_output_contract_writes_no_redundant_json_or_ply(self):
        import tempfile
        from pathlib import Path

        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            count = write_pointcloud_output(output, [(0, 0, (1.0, 2.0, 3.0), (4, 5, 6))])
            self.assertEqual(count, 1)
            self.assertEqual((output / "pointcloud.wipcld").exists(), True)
            self.assertEqual((output / "pointcloud.json").exists(), False)
            self.assertEqual((output / "pointcloud.ply").exists(), False)
        self.assertNotIn("pointcloud.json", DEFAULT_OUTPUT_FILES)
        self.assertNotIn("pointcloud.ply", DEFAULT_OUTPUT_FILES)
