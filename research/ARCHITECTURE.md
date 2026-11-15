# Current architecture understanding

## Publicly supported pipeline

`images2PosedRGBD -> atlasGenerate -> posedImages2Splats -> splats2Mesh` is the documented conceptual workflow. A posed RGBD frame is an RGB image paired with depth, camera intrinsics, and a camera-to-world extrinsic pose.

The camera model is a pinhole model. Atlas documents two local camera conventions:

- RDF: right, down, forward; camera looks along `+Z`.
- RUB: right, up, back; camera looks along `-Z`.

The pose's coordinate-system label must match the actual orientation basis; changing only the label is invalid. Depth is optical-axis depth, not Euclidean ray length. The scene scale is shared by camera positions and depth.

## Independent reconstruction boundary

The sibling prototype in `../spatial-reconstruction-lab/` only unprojects finite depth pixels into world-space points. It does not infer unseen surfaces, estimate depth, align cameras, or generate novel views. Those are separate future stages.

## Browser observations

REA is connected through the VS Code MCP registration. Passive page inspection and static bundle analysis are available through the local REA CLI. Controlled Playwright scenarios are separate from passive CDP observation and were used only to follow the public Viewfinder redirect.

## Unknown

The authenticated Atlas application, backend requests, model architecture details beyond public descriptions, splat binary format in the current product, and export implementation remain unobserved.
