import unittest

import numpy as np

from mapanything_adapter import PredictionError, prediction_summary, validate_prediction


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
