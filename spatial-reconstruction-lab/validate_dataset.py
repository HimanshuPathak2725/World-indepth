"""CLI validator for a private scene manifest."""

from __future__ import annotations

import argparse
import json

from dataset import VIEW_BUDGETS, load_manifest, select_input_views


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("manifest")
    args = parser.parse_args()
    manifest = load_manifest(args.manifest)
    print(json.dumps({
        "scene_id": manifest["scene_id"],
        "input_views": len(manifest["views"]),
        "held_out_views": len(manifest["held_out"]),
        "budgets": {
            str(budget): [view["id"] for view in select_input_views(manifest, budget)]
            for budget in VIEW_BUDGETS
        },
    }, indent=2))


if __name__ == "__main__":
    main()
