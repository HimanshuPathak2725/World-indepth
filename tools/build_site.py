"""Build the GitHub Pages payload from an explicit public allowlist."""

from __future__ import annotations

import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "_site"


def copy(source: str, destination: str) -> None:
    target = SITE / destination
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(ROOT / source, target)


def main() -> None:
    if SITE.exists():
        shutil.rmtree(SITE)
    SITE.mkdir()
    landing = (ROOT / "index.html").read_text(encoding="utf-8")
    landing = landing.replace(
        'href="spatial-reconstruction-lab/viewer/"',
        'href="viewer/"',
    )
    (SITE / "index.html").write_text(landing, encoding="utf-8")
    copy("spatial-reconstruction-lab/viewer/index.html", "viewer/index.html")
    copy("README.md", "README.md")
    copy("docs/multiview-capture.md", "docs/multiview-capture.md")
    copy("research/EXPERIMENTS.md", "research/EXPERIMENTS.md")


if __name__ == "__main__":
    main()
