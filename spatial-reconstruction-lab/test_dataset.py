import hashlib
import tempfile
import unittest
from pathlib import Path

from PIL import Image

from dataset import DatasetError, select_input_views, validate_budget_inputs


class DatasetTests(unittest.TestCase):
    def make_manifest(self, root: Path) -> dict:
        views = []
        held_out = []
        for index in range(12):
            name = f"view-{index:03d}.png"
            Image.new("RGB", (4, 3), (index, 0, 0)).save(root / name)
            digest = hashlib.sha256((root / name).read_bytes()).hexdigest()
            record = {
                "id": f"view-{index:03d}",
                "filename": name,
                "sha256": digest,
                "capture_order": index,
                "width": 4,
                "height": 3,
            }
            if index < 8:
                views.append(record)
            else:
                held_out.append(record)
        return {
            "schema_version": 1,
            "scene_id": "test-scene",
            "origin": {"type": "test", "license": "synthetic"},
            "views": views,
            "held_out": held_out,
        }

    def test_budgets_are_deterministic_and_do_not_leak(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manifest = self.make_manifest(root)
            from dataset import validate_manifest
            validate_manifest(manifest, root)
            self.assertEqual([v["id"] for v in select_input_views(manifest, 5)],
                             ["view-000", "view-002", "view-004", "view-005", "view-007"])
            validate_budget_inputs(manifest,
                                   ["view-000", "view-002", "view-004", "view-005", "view-007"], 5)
            two = {v["id"] for v in select_input_views(manifest, 2)}
            three = {v["id"] for v in select_input_views(manifest, 3)}
            five = {v["id"] for v in select_input_views(manifest, 5)}
            self.assertTrue(two < three < five)
            with self.assertRaises(DatasetError):
                validate_budget_inputs(manifest, ["view-008"], 1)

    def test_missing_image_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manifest = self.make_manifest(root)
            manifest["views"][0]["filename"] = "missing.png"
            from dataset import validate_manifest
            with self.assertRaises(DatasetError):
                validate_manifest(manifest, root)

    def test_duplicate_hash_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manifest = self.make_manifest(root)
            manifest["views"][1]["sha256"] = manifest["views"][0]["sha256"]
            from dataset import validate_manifest
            with self.assertRaises(DatasetError):
                validate_manifest(manifest, root)
