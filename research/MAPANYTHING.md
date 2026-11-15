# MapAnything integration record

## Source inspection

The upstream README at
`https://github.com/facebookresearch/map-anything/blob/main/README.md` documents
image-only inference through `MapAnything.from_pretrained`, `load_images`, and
`model.infer`. It documents outputs including `pts3d`, `pts3d_cam`, `depth_z`,
`depth_along_ray`, `intrinsics`, `camera_poses`, `conf`, and `mask`. Camera
poses use OpenCV convention: +X right, +Y down, +Z forward, camera-to-world.

The upstream code license is Apache-2.0. The selected Hugging Face model
`facebook/map-anything-apache` reports license `apache-2.0`, model SHA
`00f9c245bbcb60522d1ed7f9e9d88462c6e3f38a`, and approximately 1.23B
parameters in the Hub metadata inspected on 2026-11-15.

## Adapter boundary

`spatial-reconstruction-lab/mapanything_adapter.py` imports MapAnything only
inside the optional `run` function. It validates finite `(B,H,W,3)` point maps,
aligned confidence and masks, non-negative confidence, and records the model,
revision, coordinate convention, input hashes, runtime, and output summary.
The adapter persists only `pts3d` arrays in `predictions.npz`; confidence,
masks, poses, intrinsics, and other available outputs are summarized or listed
as not persisted. It does not guess missing fields or convert coordinate
systems.

## Current execution state

This Codespace has 2 CPUs, 7.8 GiB RAM, no GPU, and no MapAnything package.
The checkpoint was not downloaded and no real inference was attempted. The
adapter's mocked-output tests pass. A future GPU environment should install the
upstream package in an isolated Python 3.12 environment, then run
`run_mapanything.py` against a validated private manifest.

Held-out novel-view PSNR, SSIM, and LPIPS remain intentionally unset until
camera registration and a valid renderer are available.
