# Local generated outputs

Generated depth maps, point clouds, and model predictions are intentionally not
tracked. Run `run_depth.py` with an explicitly licensed local image. The compact
`pointcloud.wipcld` output is the public viewer format; it stores float32 XYZ
and uint8 RGB after a `WIPCLD01` header and count. The baseline does not write
the former redundant JSON or ASCII PLY files.
