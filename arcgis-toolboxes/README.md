# ArcGIS Toolboxes

A collection of custom Python toolboxes (`.pyt`) built for ArcGIS Pro, automating geometry and spatial-analysis workflows that would otherwise be manual or repetitive.

Each toolbox lives in its own folder with a dedicated README, the `.pyt` file, and (where applicable) a standalone demo notebook that reproduces the core logic without requiring an ArcGIS Pro license.

## Toolboxes

| Toolbox | What it does |
|---|---|
| [`three_foot_spaced_points/`](three_foot_spaced_points/) | Generates evenly spaced points (default: every 3 ft) either along a line between two points, or around the circumference of a circle defined by a center and edge point. |

## Requirements

- ArcGIS Pro (for running the actual `.pyt` tools — they depend on `arcpy`, which ships only with Esri's ArcGIS products)
- Python 3.x with `shapely`, `matplotlib`, and `jupyter` if you want to run the standalone demo notebooks (see each toolbox's README)

## Repo structure

```
arcgis-toolboxes/
├── README.md                          <- you are here
├── LICENSE
└── three_foot_spaced_points/
    ├── README.md                      <- tool-specific docs, parameters, usage
    ├── ThreeFootSpacedPoints.pyt       <- the production ArcGIS toolbox
    ├── images/                         <- screenshots / GIFs
    └── demo/
        └── geometry_demo.ipynb         <- runnable demo, no ArcGIS required
```

## About

Built and maintained as part of ongoing GIS/geospatial analysis work. New toolboxes will be added as separate folders following the same structure.
