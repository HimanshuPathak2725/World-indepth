# World-indepth

**From Pixels to Verifiable 3D Worlds.**

World-indepth is an independent, evidence-led spatial reconstruction lab. Its
first public research milestone is the **View Budget Challenge**:

> How does reconstruction quality and evidence coverage change when a static
> scene is observed in 1, 2, 3, 5, or 8 photographs?

This is not a World Labs clone or affiliation claim. The project keeps measured
outputs, model predictions, visualization assumptions, and unknowns separate.

## Repository map

- `index.html`: static research landing page.
- `spatial-reconstruction-lab/`: baseline geometry, compact point-cloud format,
  dataset validator, optional MapAnything adapter, tests, and local viewer.
- `docs/multiview-capture.md`: private scene capture and manifest contract.
- `research/`: prior public World Labs research and evidence ledger.
- `research/provenance/`: provenance for the previously inspected, but
  unverified-for-redistribution, Atlas documentation image.
- `research/artifact-manifest.json`: public/local artifact policy and compact
  format size formula.
- `.github/workflows/pages.yml`: GitHub Pages deployment workflow.

## Public-data safety

No photograph or derived reconstruction is bundled in the public demo. The
previous Atlas documentation image remains documented by URL, SHA-256, and
unknown licence status, but its image and derived outputs were removed from the
deployment payload. Private captures, checkpoints, caches, and generated
outputs are ignored by default.

The viewer accepts a local compact `WIPCLD01` file. Local files stay in the
browser and are not uploaded.

## Reproduce the single-view baseline

Use an explicitly licensed local RGB image:

```sh
cd spatial-reconstruction-lab
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python run_depth.py --image /path/to/licensed-image.webp --output output
.venv/bin/python -m unittest discover -v
```

Depth Anything V2 Small produces relative/inverse-like depth. The baseline
normalizes it to arbitrary pseudo-depth units and assumes an 80-degree
horizontal field of view. It is a single-view 2.5D point cloud, not metric
reconstruction or a complete world. Reprojection round-trip accuracy only
validates camera mathematics.

Open `spatial-reconstruction-lab/viewer/` through a local HTTP server and load
`output/pointcloud.wipcld`. The format is documented in
`spatial-reconstruction-lab/pointcloud.py`: little-endian `WIPCLD01`, uint32
point count, float32 XYZ, and uint8 RGB. It avoids the former 83 MB JSON
delivery.

## View Budget Challenge

Create a private manifest following
[`docs/multiview-capture.md`](docs/multiview-capture.md), then validate it:

```sh
cd spatial-reconstruction-lab
python validate_dataset.py private/scenes/<scene-id>/manifest.json
```

The deterministic input budgets are 1, 2, 3, 5, and 8 views; held-out images
are rejected from model input. No multi-view scene or novel-view metrics are
claimed until a real capture is supplied and held-out cameras are independently
registered.

## Optional MapAnything adapter

The adapter targets `facebook/map-anything-apache`, model revision
`00f9c245bbcb60522d1ed7f9e9d88462c6e3f38a`, Apache-2.0 metadata, and the
upstream MapAnything API. It is intentionally isolated from the baseline:

```sh
python run_mapanything.py private/scenes/<scene-id>/manifest.json \
  --budget 2 --output private/scenes/<scene-id>/outputs/budget-2 --device cuda
```

Provision the upstream MapAnything Python 3.12 environment separately with
`pip install -e .` from its repository; do not install it into the baseline
environment. The adapter's checkpoint and dependency downloads are intentionally
not part of this repository.

This Codespace has 2 CPUs, 7.8 GiB RAM, and no GPU. The checkpoint was not
downloaded and real MapAnything inference was not run here. The adapter has
mocked-output validation tests only.

## Checks

```sh
cd spatial-reconstruction-lab
python -m unittest discover -v
```

PSNR, SSIM, and LPIPS are deliberately not reported until held-out camera
registration and valid comparable rendering exist.
