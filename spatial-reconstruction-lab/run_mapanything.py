"""Run the optional MapAnything adapter on a validated input subset."""

from __future__ import annotations

import argparse
import json

from dataset import load_manifest, select_input_views
from mapanything_adapter import run


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("manifest")
    parser.add_argument("--budget", type=int, choices=(1, 2, 3, 5, 8), required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--device", default="cuda")
    args = parser.parse_args()
    manifest = load_manifest(args.manifest)
    selected = select_input_views(manifest, args.budget)
    root = __import__("pathlib").Path(args.manifest).parent
    metadata = run([str(root / view["filename"]) for view in selected], args.output, args.device)
    metadata["scene_id"] = manifest["scene_id"]
    metadata["input_view_ids"] = [view["id"] for view in selected]
    from pathlib import Path
    Path(args.output, "metadata.json").write_text(json.dumps(metadata, indent=2) + "\n")
    print(json.dumps(metadata, indent=2))


if __name__ == "__main__":
    main()
