# Experiments

## A0 — synthetic RGB-D unprojection

Status: passed.

The prototype validates the documented RDF and RUB optical-axis equations and applies a camera-to-world rigid transform to finite depth pixels. A NaN depth value is skipped. Tests use a 3x2 synthetic depth grid and a translated camera, so the result checks both pixel-centering and pose translation.

Command:

```sh
python3 -m unittest discover -s ../spatial-reconstruction-lab
```

Result: 4 tests passed.

## A1 — public Viewfinder boundary

Status: passed with access boundary.

The public Viewfinder URL was opened in a provider-owned Chromium 156 scenario. It redirected to the sign-in page before an upload control or generation workflow could be reached. No account credentials, API key, upload, or paid task was used.

## A2 — real single-image reconstruction

Status: passed with explicit relative-depth limitations.

The official Atlas documentation image was downloaded directly from
`https://docs.atlas.worldlabs.ai/media/how-to-use-atlas-source.webp` after
inspection of `https://docs.atlas.worldlabs.ai/how-to-use-atlas`. It is a
1280x720 WEBP depicting a blacksmith workshop. The page does not establish
whether it is a photograph, AI-generated image, or 3D render; that uncertainty
is preserved in `../spatial-reconstruction-lab/assets/input/source_metadata.json`.
SHA-256:
`beb7affa5068e1e35b7cb25e84b9ba14ec09c7d5bb51eec0559c91ab93b58b48`.

The isolated `../spatial-reconstruction-lab/.venv` ran
`depth-anything/Depth-Anything-V2-Small-hf` revision
`5426e4f0f36572d16453bbda7a8389317b1bef99` on CPU. The model completed in
4.51 seconds and produced a 1280x720 finite prediction. Its relative,
inverse-like output was min-max normalized and inverted into arbitrary
pseudo-depth units `[1, 5]`; these values are not metres. An assumed 80-degree
horizontal field of view supplied `fx=fy=762.7223` and the image-centre
principal point.

Generated artifacts:

- `output/depth.npy`
- `output/depth_visualization.png`
- `output/pointcloud.ply`
- `output/pointcloud.json`
- `output/camera.json`
- `output/metrics.json`

The RGB-D projection produced 921,600 colour-aligned finite points. Reprojecting
those same points through the assumed camera returned a maximum error of
`1.27e-13` pixels. This is mathematical round-trip accuracy only; it is not
evidence that the estimated depth is accurate.

## A3 — interactive reconstruction viewer

Status: passed.

`viewer/index.html` was served with `python3 -m http.server 8765` and loaded in
the installed Playwright Chromium. The page reported
`921,600 points; relative depth; arbitrary scale`, created one WebGL canvas,
and exposed the point-size slider and reset-camera button. A browser import map
was required so Three.js `OrbitControls` could resolve its `three` dependency.
The viewer supports orbit, zoom, camera translation through OrbitControls, reset,
point-size adjustment, source-image display, and depth visualization. It
visualizes a single-view 2.5D cloud; disocclusions, back surfaces, and depth
errors remain limitations rather than reconstructed geometry.
