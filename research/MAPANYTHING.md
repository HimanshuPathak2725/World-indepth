# MapAnything integration record

## Source inspection

The upstream README and source at commit
`3d10cf7a3016fc0f9bb13a071ee66c47b10be0d9` document image-only inference
through `MapAnything.from_pretrained`, `load_images`, and `model.infer`. The
documented prediction contract also includes `cam_trans` and `cam_quats`.
Camera poses use OpenCV convention: +X right, +Y down, +Z forward,
camera-to-world.

The upstream code license is Apache-2.0. The selected Hugging Face model
`facebook/map-anything-apache` reports license `apache-2.0`, checkpoint
revision `00f9c245bbcb60522d1ed7f9e9d88462c6e3f38a`, and approximately 1.23B
parameters in the inspected Hub metadata.

## Adapter boundary

`spatial-reconstruction-lab/mapanything_adapter.py` imports MapAnything only
inside the optional `run` function. It validates finite `(B,H,W,3)` point maps,
aligned confidence and masks, non-negative confidence, and records the model,
revisions, coordinate convention, input hashes, runtime, and output summary.
A successful run requires the complete documented output set:
`pts3d`, `pts3d_cam`, `depth_z`, `depth_along_ray`, `intrinsics`,
`camera_poses`, `cam_trans`, `cam_quats`, `conf`, and `mask`. All validated
tensors are moved to CPU and persisted as compressed arrays in
`predictions.npz`; no output is silently discarded.

## Current execution state

This Codespace has 2 CPUs, 7.8 GiB RAM, no GPU, and no MapAnything package.
The checkpoint was not downloaded and no real inference was attempted. The
adapter's mocked-output tests pass. The reproducible Colab entry point is
[`notebooks/01_colab_view_budget.ipynb`](../notebooks/01_colab_view_budget.ipynb);
it checks for a GPU, installs the pinned upstream source, passes the pinned
checkpoint revision to the loader, and runs the two-view smoke test before any
full view budget.

Held-out novel-view PSNR, SSIM, and LPIPS remain intentionally unset until
camera registration and a valid renderer are available.
