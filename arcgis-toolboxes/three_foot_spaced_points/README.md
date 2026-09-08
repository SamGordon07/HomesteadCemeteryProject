# 3-Foot Spaced Points

An ArcGIS Pro Python toolbox that generates evenly spaced points (default: every 3 feet) either:

- **along a straight line** between two existing points, or
- **around the circumference of a circle** defined by a center point and an edge point.

Points that would fall within 2 feet of a line's endpoints are automatically skipped, to avoid clutter right at the anchor points.

## Why this exists

Built for a workflow where field/survey points needed to be densified at a fixed interval for downstream analysis — rather than manually placing dozens of points by hand for every segment or ring, this tool generates them in bulk from a simple OBJECTID reference.

## Files

| File | Purpose |
|---|---|
| `ThreeFootSpacedPoints.pyt` | The ArcGIS Pro Python toolbox — the actual production tool. Requires ArcGIS Pro (uses `arcpy`). |
| `demo/geometry_demo.ipynb` | A standalone Jupyter notebook that reimplements the same math with `shapely` + `matplotlib`, no ArcGIS license required. Run this to see the algorithm work without installing anything but Python. |
| `images/` | Screenshots / GIFs of the tool running inside ArcGIS Pro (see below). |

## How it works

### Line mode
Given a semicolon-separated list of OBJECTID pairs (e.g. `1,2;3,4`), the tool:
1. Looks up each point's coordinates from the input feature class.
2. Draws a straight line between each pair.
3. Walks along that line in 3-foot increments, dropping a point at each step — except for points that land within 2 feet of either endpoint.

### Circle mode
Given a center point OBJECTID and an edge point OBJECTID:
1. Computes the radius as the straight-line distance between the two points.
2. Computes the angular step needed so that consecutive points are ~3 feet apart along the circumference (`angle_step = spacing / radius`).
3. Places points around the full circle at that angular step, and closes the loop with a polyline.

Both modes can be used in the same run — pairs and a circle aren't mutually exclusive.

## Parameters

| # | Name | Type | Required | Notes |
|---|---|---|---|---|
| 0 | Input Feature Class | Feature Layer | Yes | Source points, referenced by OBJECTID. |
| 1 | Output Line Feature Class | Feature Class | Yes | Where generated lines are written. |
| 2 | Output Points Feature Class | Feature Class | Yes | Where generated points are written. |
| 3 | Pairs of OBJECTIDs | String | Optional* | Format: `OID1,OID2;OID3,OID4;...` |
| 4 | Circle Center Point OBJECTID | Long | Optional* | Used with param 5 for circle mode. |
| 5 | Circle Edge Reference Point OBJECTID | Long | Optional* | Defines the radius together with param 4. |

\* At least one of "Pairs" or the "Circle" pair (4 + 5) must be provided.

## Installation / usage

1. Requires **ArcGIS Pro** (tested on Pro 3.x) — `arcpy` is not available outside ArcGIS installations.
2. In ArcGIS Pro: **Insert → Toolbox → Add Toolbox**, and select `ThreeFootSpacedPoints.pyt`. (Or just drag the file into the Catalog pane.)
3. Open the "Generate Points at 3-Foot Intervals" tool from the toolbox.
4. Fill in the input feature class and desired outputs, plus either OBJECTID pairs, a center/edge pair, or both.
5. Run.

## Screenshots



## Try the logic without ArcGIS

See [`demo/geometry_demo.ipynb`](demo/geometry_demo.ipynb) — it reproduces the line-spacing and circle-spacing math with `shapely` and plots the results, so you can see it work without an ArcGIS Pro license.
