import unittest
import tempfile
from pathlib import Path

import numpy as np

from mapanything_adapter import (
    PredictionError,
    prediction_summary,
    save_predictions,
    validate_complete_prediction,
    validate_prediction,
)


class MapAnythingAdapterTests(unittest.TestCase):
    def test_valid_prediction_summary_preserves_confidence_statistics(self):
        prediction = {
            "pts3d": np.zeros((1, 2, 2, 3), dtype=np.float32),
            "conf": np.array([[[1.0, 2.0], [3.0, 4.0]]]),
            "mask": np.array([[[True, False], [True, True]]]),
        }
        validate_prediction(prediction)
        summary = prediction_summary([prediction])
        self.assertEqual(summary["valid_point_count"], 3)
        self.assertEqual(summary["confidence"]["mean"], 8 / 3)

    def test_persistence_keeps_documented_outputs(self):
        prediction = {
            "pts3d": np.zeros((1, 2, 2, 3), dtype=np.float32),
            "pts3d_cam": np.ones((1, 2, 2, 3), dtype=np.float32),
            "depth_z": np.ones((1, 2, 2, 1), dtype=np.float32),
            "depth_along_ray": np.ones((1, 2, 2, 1), dtype=np.float32),
            "intrinsics": np.eye(3, dtype=np.float32)[None],
            "camera_poses": np.eye(4, dtype=np.float32)[None],
            "cam_trans": np.zeros((1, 3), dtype=np.float32),
            "cam_quats": np.zeros((1, 4), dtype=np.float32),
            "conf": np.ones((1, 2, 2), dtype=np.float32),
            "mask": np.ones((1, 2, 2, 1), dtype=bool),
        }
        with tempfile.TemporaryDirectory() as directory:
            keys = save_predictions([prediction], directory)
            saved = np.load(Path(directory) / "predictions.npz")
            self.assertEqual(len(keys), 10)
            self.assertEqual(saved["view_0_camera_poses"].shape, (1, 4, 4))
            self.assertEqual(saved["view_0_mask"].shape, (1, 2, 2, 1))

    def test_complete_validation_rejects_missing_evidence_outputs(self):
        prediction = {
            "pts3d": np.zeros((1, 1, 1, 3)),
            "conf": np.ones((1, 1, 1)),
            "mask": np.ones((1, 1, 1)),
        }
        with self.assertRaises(PredictionError):
            validate_complete_prediction(prediction)

    def test_complete_validation_rejects_malformed_camera_output(self):
        prediction = {
            "pts3d": np.zeros((1, 1, 1, 3)),
            "pts3d_cam": np.zeros((1, 1, 1, 3)),
            "depth_z": np.zeros((1, 1, 1, 1)),
            "depth_along_ray": np.zeros((1, 1, 1, 1)),
            "intrinsics": np.zeros((1, 3, 3)),
            "camera_poses": np.zeros((1, 3, 4)),
            "cam_trans": np.zeros((1, 3)),
            "cam_quats": np.zeros((1, 4)),
            "conf": np.ones((1, 1, 1)),
            "mask": np.ones((1, 1, 1)),
        }
        with self.assertRaises(PredictionError):
            validate_complete_prediction(prediction)

    def test_invalid_shapes_are_rejected(self):
        with self.assertRaises(PredictionError):
            validate_prediction({
                "pts3d": np.zeros((2, 2, 3)),
                "conf": np.zeros((1, 2, 2)),
                "mask": np.ones((1, 2, 2)),
            })

    def test_nonfinite_points_are_rejected(self):
        prediction = {
            "pts3d": np.zeros((1, 1, 1, 3)),
            "conf": np.ones((1, 1, 1)),
            "mask": np.ones((1, 1, 1)),
        }
        prediction["pts3d"][0, 0, 0, 0] = np.nan
        with self.assertRaises(PredictionError):
            validate_prediction(prediction)
