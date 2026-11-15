# World Labs research handoff

Updated: 2026-11-15

## Completed

- Verified REA fork checkout at `664fab7470c0138f39033aeac07fc54ba917f067`.
- Installed locked dependencies and built REA successfully.
- Applied the scoped VS Code MCP registration at `/home/codespace/.config/Code/User/mcp.json`; `rea doctor --client vscode --json` reports the registration aligned.
- Installed Chromium 156 through the repository's existing `playwright-core` tooling and its runtime dependencies. The browser runs on loopback CDP port 9222.
- Captured the public `https://worldlabs.ai/` page and analyzed its loaded Next.js bundle.
- Ran a controlled public Viewfinder scenario. The unauthenticated workflow redirects to `https://atlas.worldlabs.ai/sign-in?redirect=%2Fworkflows%2Fviewfinder`.
- Added the CPU-only RGB-D projection pipeline in `../spatial-reconstruction-lab/`.
- Downloaded and provenance-recorded the public Atlas documentation workshop image.
- Ran Depth Anything V2 Small CPU inference and generated the depth, visualization, camera, metrics, JSON cloud, and PLY artifacts.
- Validated the interactive Three.js viewer in local Playwright Chromium after adding an import map for `OrbitControls`.
- Created the `feat/view-budget-challenge` branch with public-data safety,
  compact point-cloud delivery, a private multi-view dataset contract, a
  tested optional MapAnything adapter, a static landing page, and a GitHub
  Pages workflow.

## Evidence

- World Labs page inspection: `ev_2e7169050ab897bef19fb858dfe9c4e650ee96e2f535ff4f8b8c20f9885c093b`
- World Labs bundle route view: `ev_06cccc5371127f29fd4656d1342792b771006bbb5726025af07e2e25c0574a20`; parent bundle evidence `ev_68447a844cac79938d2c274624e59f28e60ef44e3712370c028add66c1224a02`
- Viewfinder sign-in boundary: `ev_a508aca91fb67eb2062df542daca13e6d449039f5de4583b3281527c83c96c27`; complete bundle `/tmp/worldlabs-viewfinder-evidence.json`

## Exact commands and results

- `npm ci`: passed; 742 packages installed, npm reported 7 moderate audit findings.
- `npm run build:cached`: passed; 3 Turborepo tasks successful.
- `node scripts/rea.mjs setup --client vscode --dry-run --json`: produced a plan targeting `/home/codespace/.config/Code/User/mcp.json`.
- `node scripts/rea.mjs setup --client vscode --yes --json`: passed.
- `node scripts/rea.mjs doctor --client vscode --json`: VS Code registration and skill aligned; native engines are intentionally unconfigured.
- `node scripts/rea.mjs list-browser-targets http://127.0.0.1:9222 --json`: passed; observed `https://worldlabs.ai/`.
- `node scripts/rea.mjs inspect-web-page ...`: passed; complete output saved at `/tmp/worldlabs-page.json`.
- `node scripts/rea.mjs analyze-web-bundle ...`: passed; complete output saved at `/tmp/worldlabs-bundle-evidence.json`.
- `node scripts/rea.mjs capture-browser-scenario ...`: passed; Viewfinder redirect captured.
- `python3 -m unittest discover -s ../spatial-reconstruction-lab`: passed; 7 tests.
- `cd ../spatial-reconstruction-lab && OMP_NUM_THREADS=2 MKL_NUM_THREADS=2 .venv/bin/python run_depth.py --image assets/input/world-labs-workshop.webp --output output`: passed; 4.51 seconds, 921,600 points, zero invalid pixels.
- Generated artifact integrity check: passed; depth shape, visualization dimensions, PLY header/count, JSON point count, finite depth, and RGB/XYZ field shapes verified.
- `cd ../spatial-reconstruction-lab && python3 -m http.server 8765`: served viewer successfully.
- Playwright Chromium viewer load: passed; status reported 921,600 points, one canvas, two controls; screenshot saved at `/tmp/spatial-reconstruction-viewer.png`.
- The prior Atlas-derived image, generated outputs, and validation screenshot
  were removed from the public payload because redistribution was unverified;
  provenance remains in `research/provenance/`.
- MapAnything upstream README and Apache checkpoint metadata were inspected.
  The adapter is implemented and mocked-output-tested; no checkpoint download or
  real inference was performed because this host has no GPU.

## Blockers and limitations

- No authenticated World Labs account or API key was used. Upload, generation, export, and paid API behavior remain unobserved.
- The public site bundle provides static route candidates, not proof of backend endpoints or reachability.
- The source page does not establish whether the selected workshop visual is a photograph, AI-generated image, or 3D render; it is recorded as unknown rather than called a photograph.
- No GPU is present; the Codespace reports 2 CPUs and 7.8 GiB RAM.
- Depth is relative/inverse-like and normalized to arbitrary pseudo-depth units; metric scale and geometric accuracy are unknown.
- The viewer is a single-view 2.5D visualization, not a complete world reconstruction; holes, disocclusion, back surfaces, and depth errors remain.
- The first `pytest` attempt failed because `pytest` is not installed in the isolated venv; the existing `unittest` suite passed instead. No dependency was added.
- No real private multi-view scene, held-out split, camera registration, or
  PSNR/SSIM/LPIPS evaluation exists yet.
- `rea doctor` reports Hopper, Ghidra, IDA, JADX, and Kuna unavailable; none is needed for the browser investigation.

## Exact next action

Use the generated local artifacts and viewer for qualitative inspection, and compare
their documented representation with Atlas's public posed-RGBD contract. An
authorized Viewfinder experiment remains unavailable without legitimate access;
do not bypass sign-in or make paid generation requests.

For the next milestone, capture one licensed static indoor scene with at least
12 overlapping photographs: 8 possible input views and 4 held-out views. Keep
the photographs in the ignored `private/scenes/` tree.
