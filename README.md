# World-indepth

**From Pixels to Verifiable 3D Worlds.**

World-indepth is an independent, open-source project exploring how multiple images can be used to build inspectable 3D representations of real scenes.

The current focus is the **View Budget Challenge**:

> What changes when a scene is observed using 1, 2, 3, 5, or 8 input photographs?

The goal is not just to generate a visually convincing point cloud. It is to preserve the evidence behind a reconstruction: input images, camera information, confidence, geometry, and the assumptions made along the way.

This is an independent project, not a World Labs clone or an affiliated project.

---

## Current progress

### First multi-view MapAnything experiment

On November 15, 2026, I ran the first complete multi-view experiment using the ETH3D Pipes scene and the Apache-licensed MapAnything checkpoint.

The experiment was executed on a Google Colab **Tesla T4 GPU**.

| Configuration | Value |
|---|---|
| Model | `facebook/map-anything-apache` |
| Checkpoint revision | `00f9c245bbcb60522d1ed7f9e9d88462c6e3f38a` |
| MapAnything source revision | `3d10cf7a3016fc0f9bb13a071ee66c47b10be0d9` |
| Input resolution | 392 px longest side |
| Actual model input | 392 × 266 |
| GPU | NVIDIA Tesla T4 |
| CUDA | 13.0 |
| PyTorch | 2.14.1+cu130 |
| Mixed precision | BF16 |

The experiment tested five input budgets using the same resolution and deterministic nested input selection.

| Input views | Inference time | Peak allocated VRAM | Mask-valid point samples |
|---:|---:|---:|---:|
| 1 | 0.93 s | 4.80 GiB | 90,414 |
| 2 | 1.79 s | 4.90 GiB | 185,602 |
| 3 | 2.70 s | 5.23 GiB | 272,495 |
| 5 | 4.64 s | 6.23 GiB | 444,003 |
| 8 | 7.28 s | 8.59 GiB | 713,637 |

The one-time checkpoint loading took approximately 274 seconds. The inference times above exclude that initial loading time.

All five view budgets completed successfully.

**Important:** The point counts are sums of valid pixels across the individual per-view prediction masks. They are not unique scene points, fused surface coverage, or a measure of reconstruction accuracy. Overlapping views can represent the same physical surface.

### What the model returned

The Colab experiment saved model outputs including:

- World-coordinate point maps (`pts3d`)
- Camera-coordinate point maps (`pts3d_cam`)
- Predicted camera poses and intrinsics
- Confidence maps and masks
- Depth along the camera axis and viewing ray
- Ray directions and image data
- Per-view metadata, input hashes, and run configuration

The experiment also generated compact `WIPCLD01` point-cloud previews for visualization.

These previews contain points from individual view predictions. They are not yet a deduplicated, confidence-aware fused reconstruction.

Four designated held-out images were excluded from model inference. They have not yet been used for a valid novel-view evaluation.

---

## What is implemented

The repository currently contains two separate paths.

### 1. Single-view baseline

The baseline uses [Depth Anything V2 Small](https://huggingface.co/depth-anything/Depth-Anything-V2-Small-hf) to estimate relative depth from one RGB image.

The pipeline is:

```text
RGB Image
    |
    v
Depth Anything V2 Small
    |
    v
Relative / inverse-like depth
    |
    v
Depth normalization
    |
    v
RGB-D unprojection
    |
    v
WIPCLD01 point cloud
    |
    v
Three.js viewer
```

Depth is normalized into arbitrary pseudo-depth units. An 80-degree horizontal field of view is assumed by default.

This is a **single-view 2.5D representation**, not metric reconstruction. Reprojection tests verify the camera mathematics, not the accuracy of the predicted depth.

### 2. Multi-view tooling

The repository also contains the initial infrastructure for multi-view experiments:

- Private scene manifests with image hashes and dimension checks.
- Held-out image leakage validation.
- Deterministic input selection for 1, 2, 3, 5, and 8 views.
- An optional MapAnything inference adapter.
- Prediction validation for point maps, masks, and confidence.
- Camera-to-world coordinate convention metadata.
- Compact point-cloud serialization.
- A local browser-based point-cloud viewer.

The current Python MapAnything adapter is still an initial integration: it persists `pts3d` to `predictions.npz` and records other available outputs as not persisted. Its default image loader also does not explicitly reproduce the 392px preprocessing used in the Colab experiment.

The full-output saving and 392px preprocessing used in the experiment notebook have not yet been integrated into the repository CLI.

---

## Repository structure

```text
World-indepth/
│
├── index.html
├── README.md
│
├── docs/
│   └── multiview-capture.md
│
├── research/
│   ├── EXPERIMENTS.md
│   ├── MAPANYTHING.md
│   ├── provenance/
│   └── artifact-manifest.json
│
├── spatial-reconstruction-lab/
│   ├── dataset.py
│   ├── validate_dataset.py
│   ├── mapanything_adapter.py
│   ├── run_mapanything.py
│   ├── run_depth.py
│   ├── pointcloud.py
│   ├── requirements.txt
│   ├── test_mapanything_adapter.py
│   └── viewer/
│
└── .github/
    └── workflows/
        └── pages.yml
```

---

## Getting started

Clone the repository:

```bash
git clone https://github.com/HimanshuPathak2725/World-indepth.git
cd World-indepth
```

### Run the single-view baseline

Create an isolated environment:

```bash
cd spatial-reconstruction-lab

python3 -m venv .venv

# Linux / macOS
source .venv/bin/activate

# Windows PowerShell
# .venv\Scripts\Activate.ps1

python -m pip install -r requirements.txt
```

Run depth estimation on a licensed RGB image:

```bash
python run_depth.py \
  --image /path/to/image.webp \
  --output output/
```

The output directory contains:

```text
output/
├── depth.npy
├── depth_visualization.png
├── pointcloud.wipcld
├── camera.json
└── metrics.json
```

The point cloud uses arbitrary pseudo-depth units, not metres.

### Validate a multi-view scene

The multi-view tooling expects a private scene manifest. See [`docs/multiview-capture.md`](docs/multiview-capture.md) for the schema and directory layout.

Validate it with:

```bash
python validate_dataset.py private/scenes/<scene-id>/manifest.json
```

### Run the optional MapAnything adapter

MapAnything requires its own model dependencies and a suitable GPU environment.

After provisioning the upstream package, run:

```bash
python run_mapanything.py \
  private/scenes/<scene-id>/manifest.json \
  --budget 2 \
  --output private/scenes/<scene-id>/outputs/budget-2 \
  --device cuda
```

Supported budgets are `1`, `2`, `3`, `5`, and `8`.

This CLI is an initial adapter, not yet an exact reproduction of the Colab experiment configuration described above.

---

## Point-cloud format

The project uses a compact binary format called `WIPCLD01`.

| Field | Encoding |
|---|---|
| Magic | 8-byte ASCII `WIPCLD01` |
| Point count | Little-endian uint32 |
| Position | Three little-endian float32 values |
| Colour | Three uint8 RGB values |

Each point record occupies 15 bytes.

The local viewer loads these files directly in the browser. The file is not uploaded to a server.

---

## Dataset and model provenance

The multi-view experiment used the **ETH3D Pipes** scene.

- Dataset: [ETH3D](https://eth3d.ethz.ch/datasets)
- Dataset licence: [CC BY-NC-SA 4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/)
- Model: [MapAnything Apache checkpoint](https://huggingface.co/facebook/map-anything-apache)
- Upstream source: [facebookresearch/map-anything](https://github.com/facebookresearch/map-anything)
- Checkpoint revision: `00f9c245bbcb60522d1ed7f9e9d88462c6e3f38a`
- Source revision: `3d10cf7a3016fc0f9bb13a071ee66c47b10be0d9`

The ETH3D images and derived experiment artifacts are kept outside the public repository. Their use and any redistribution must respect the dataset's non-commercial and share-alike requirements.

---

## Current limitations

The successful inference runs are an important implementation milestone, but several research questions remain open.

- Per-view point maps have not yet been deduplicated and fused into a consistent scene.
- Confidence-aware filtering and geometric consistency need a reproducible implementation.
- Point support across views has not yet been established through visibility or geometric correspondence.
- Metric scale and geometric accuracy have not been independently validated.
- Held-out cameras have not been independently registered for comparable novel-view rendering.
- PSNR, SSIM, LPIPS, and Chamfer-distance accuracy are therefore not reported.
- The current CLI adapter does not yet persist all the model outputs saved by the Colab experiment.

A larger point count or a visually appealing point cloud is not, by itself, evidence of better reconstruction quality.

---

## Next milestone

**Confidence-aware multi-view fusion.**

The next stage is to combine the per-view world-coordinate point maps while retaining:

1. Source-view and pixel provenance.
2. Confidence and validity information.
3. Camera-pose consistency.
4. Geometric support across views.
5. Reproducible fusion parameters.

After that, the project can move towards geometric evaluation using the appropriate ETH3D ground-truth resources.

---

## Tests

Run the CPU-side test suite:

```bash
cd spatial-reconstruction-lab
python -m unittest discover -v
```

The tests cover the baseline projection mathematics, compact point-cloud format, dataset validation, and mocked MapAnything prediction validation.

---

**World-indepth is a work in progress.** The focus is on building a reproducible path from images to inspectable 3D evidence, one experiment at a time.
