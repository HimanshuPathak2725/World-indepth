# World-indepth

Evidence-led research into World Labs public workflows and an independent
single-image RGB-D reconstruction prototype.

## What is included

- `spatial-reconstruction-lab/`: CPU depth inference, RGB-D unprojection,
  generated artifacts, focused tests, and a browser viewer.
- `research/`: architecture, evidence ledger, experiment log, handoff, and
  unresolved questions.
- `research/evidence/rea/`: retained public World Labs browser observations.
- `research/evidence/spatial-reconstruction-viewer.png`: local viewer validation
  screenshot.

The REA source repository itself is intentionally not copied here. It was used
as the local observation instrument.

## Reproduce the reconstruction

The checked-in outputs are the results of the completed run. To reproduce
inference without modifying REA dependencies:

```sh
cd spatial-reconstruction-lab
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
OMP_NUM_THREADS=2 MKL_NUM_THREADS=2 .venv/bin/python run_depth.py \
  --image assets/input/world-labs-workshop.webp \
  --output output
```

The model is `depth-anything/Depth-Anything-V2-Small-hf`. Its output is
relative/inverse-like depth. The script explicitly normalizes it into arbitrary
pseudo-depth units and does not claim metres or metric accuracy.

Run the focused geometry tests:

```sh
.venv/bin/python -m unittest -v test_pointcloud.py
```

Serve and open the viewer:

```sh
python3 -m http.server 8765
# open http://127.0.0.1:8765/viewer/
```

The viewer uses Three.js from jsDelivr and therefore needs network access to
load its browser modules. It supports orbiting, zooming, translation, reset,
point-size adjustment, and comparison with the source image and depth map.

## Input provenance and limitations

The input is the public Atlas documentation image recorded in
`assets/input/source_metadata.json`. Its page describes a blacksmith workshop,
but does not establish whether the visual is a photograph, AI-generated image,
or 3D render. Licence or reuse permission was not verified; the local copy is
retained for research and is not presented as original work.

This is a single-view 2.5D reconstruction. It cannot recover unseen surfaces,
disocclusions, or reliable metric scale. Reprojection error validates the
internal camera mathematics, not the quality of the estimated depth.

No authenticated Viewfinder workflow, upload, generation, export, or paid API
request was performed.
