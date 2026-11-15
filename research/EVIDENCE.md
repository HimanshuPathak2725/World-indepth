# Evidence ledger

## Observed

| Claim | Evidence | Reproduction and limitation |
|---|---|---|
| The public World Labs landing page describes Atlas as turning images into explorable worlds and links to Viewfinder, Chisel, splat-to-mesh, relighting, and API workflows. | `web_fetch https://worldlabs.ai/` on 2026-11-15 | Public page content only; not a claim about authenticated availability. |
| The public Atlas page presents Viewfinder as image-based reconstruction and camera exploration, and links API documentation. | `web_fetch https://worldlabs.ai/atlas` on 2026-11-15 | Public marketing/documentation surface. |
| Opening `https://atlas.worldlabs.ai/workflows/viewfinder` without credentials redirects to `/sign-in?redirect=%2Fworkflows%2Fviewfinder`. | REA controlled replay `ev_a508aca91fb67eb2062df542daca13e6d449039f5de4583b3281527c83c96c27` | One clean Chromium 156 replay; no authentication attempted. |
| The World Labs public site loaded a Next.js page bundle with static route candidates including `/`, `/about`, `/atlas`, `/blog`, and `/labs`. | REA bundle route view `ev_06cccc5371127f29fd4656d1342792b771006bbb5726025af07e2e25c0574a20` | Static candidates are not runtime reachability or complete route inventory. |
| The official Atlas documentation exposes a 1280x720 WEBP blacksmith-workshop image at `https://docs.atlas.worldlabs.ai/media/how-to-use-atlas-source.webp`. | `source_metadata.json`, SHA-256 `beb7affa5068e1e35b7cb25e84b9ba14ec09c7d5bb51eec0559c91ab93b58b48` | Public asset and page description establish provenance and dimensions; visual type and licence remain unknown/unverified. |
| Depth Anything V2 Small completed CPU inference on the local reference image in 4.51 seconds, with finite 1280x720 output and no invalid pixels. | `../spatial-reconstruction-lab/output/metrics.json` | Model output is relative/inverse-like; no metric-depth accuracy claim follows. |
| RGB-D unprojection generated 921,600 finite colour-aligned points and reprojected them with maximum error `1.27e-13` pixels. | `../spatial-reconstruction-lab/output/metrics.json`; 7 projection unit tests | Round-trip tests validate implementation consistency, not depth-estimation quality or complete 3D coverage. |
| The local viewer loaded the generated cloud in Chromium and exposed its canvas, point-size control, reset control, source image, and depth visualization. | Browser load at `http://127.0.0.1:8765/viewer/`, screenshot `/tmp/spatial-reconstruction-viewer.png` | Browser validation was local and headless; no claim is made about hosted deployment. |

## Documented

| Claim | Source |
|---|---|
| Atlas `images2PosedRGBD` estimates cameras and linear depth; one image uses a single-view path and multiple images use a multi-view path. | https://docs.atlas.worldlabs.ai/images-to-posed-images |
| Atlas camera extrinsics are camera-to-world, quaternions are XYZW, and cameras declare `rub` or `rdf`. | https://docs.atlas.worldlabs.ai/cameras-and-posed-images |
| RGB, depth, camera intrinsics, and confidence must remain aligned to the same grid; resizing requires scaling intrinsics and cropping requires shifting the principal point. | https://docs.atlas.worldlabs.ai/cameras-and-posed-images |
| Depth is along the camera viewing axis; RUB unprojection is `((u-cx)/fx*z, -(v-cy)/fy*z, -z)`. Non-finite depth means no reliable geometry. | https://docs.atlas.worldlabs.ai/cameras-and-posed-images |
| `atlasGenerate` takes posed RGBD context and target cameras; `returnDepth` can make generated views reusable context. | https://docs.atlas.worldlabs.ai/atlas-generate |

## Inferences and unknowns

- Atlas's public staged workflow strongly supports a posed-RGBD intermediate, but the public material does not prove that every internal model call is implemented as those exact stages.
- The public site does not establish backend API URLs, request bodies, authorization behavior beyond the sign-in boundary, or model internals.
