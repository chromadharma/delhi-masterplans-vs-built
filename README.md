# Delhi's master plans against the built city

Delhi's three statutory land-use plans — **MPD 1962**, **MPD 2001** and the **Draft MPD 2041** — georeferenced onto one grid and tested against satellite-derived building footprint for every five years from 1975 to 2030.

Interactive page: **https://claude.ai/artifact/26LVXyuiXMmMck6P6fSu4f**
Analysis and maps by **Sahasrik Ragani**, September 2026.

## Findings

| | 1975–2000 | 2000–2020 | 1975–2020 |
|---|---|---|---|
| New building surface ≥400 m **outside the 1962 plan's urban limit** | 55% | 60% | **57%** |
| New building surface ≥400 m **outside the 2001 plan's urban limit** | 49% | 39% | **46%** |

- Delhi's building footprint grew from **182 km² (1975) to 290 km² (2020)**. GHSL measures roof area, not urban extent.
- Planned housing, work, institutional and park land: **~392 km² (1962) → 441 km² (2001) → 605 km² (2041 draft)**. The 2041 draft leaves a further ~390 km² in six land-pooling zones (N, P-I, P-II, K-I, L, J) to be planned later.
- The 2041 draft keeps **210 km² of green belt** (14% of Delhi), so the rural/urban distinction is not erased.
- By 2020, **22.1 km² of the 2041 green belt's interior** (14%) and **6.1 km² of the Ridge** (10%) were already built-up at GHSL's 100 m cell scale. The draft itself maps **106.6 km² of unauthorized colonies**, 10.7 km² of them on land it zones green belt.

## Accuracy

| Sheet | Method | Residuals |
|---|---|---|
| Draft 2041 | 4,347 vector polygons from the PDF; silhouette fitted to the OSM Delhi boundary | median 66 m; fitted scale within 0.03% of the sheet's scale bar |
| MPD 2001 | Drawn territory boundary (ICP) + 3 landmarks | boundary median ~50 m; landmarks 130–300 m |
| MPD 1962 | 10 control points (monuments, boundary corners, a rail line) | 40–370 m; held-out Qutub check 445 m |

The 1962 base map was surveyed and drawn before satellite imagery, so a few hundred metres of drift is expected. Usable at city scale, not for parcel-level claims.

Land-use classification of the two scans (colour enhancement → clustering → manual class assignment) scored **81%** (1962, n=42) and **86%** (2001, n=36) against visual labels on stratified random points. Residential and commercial/industrial were correct in every sample; most errors are parks vs public land and water. 2041 classes are exact, straight from the vectors. Commercial and industrial are merged into one class because the 1962 maroons cannot be separated reliably.

## Layout

```
Delhi_Masterplans_aligned.qgz   QGIS project (EPSG:32643), 29 styled layers
rasters/     harm_{1962,2001,2041}.tif   common classes (see codes below)
             limit_{1962,2001}.tif       1 = inside urban limit, 2 = >=400 m outside, 0 = exclusion ring
             mpd2041_classes_utm43.tif   exact 2041 classes from the PDF vectors
             mpd2041_unauth_utm43.tif    unauthorized colonies
vectors/     mpd2041_vectors.gpkg        planning zones, rail, transit, Yamuna outline, colonies
             nct_boundary_osm.geojson
ghsl/        GHS-BUILT-S R2023A clips, 100 m, 1975–2030 (2025/2030 are projections)
results/     areas, limits, cross-tabs, accuracy, fitted transforms (JSON)
scripts/     the pipeline, in run order (below)
docs/         the published page and its map layers (served by GitHub Pages)
```

Common class codes: `0` uncoloured (rural, transport, hatched uses) · `1` residential · `2` commercial & industrial · `3` public, semi-public & government · `4` parks & recreation · `5` green belt & agriculture · `6` water & floodplain · `255` outside sheet or outside Delhi.

Analysis grid: EPSG:32643, 10 m, x 678000–731000, y 3142000–3198000.

## Reproducing

The three source PDFs are DDA publications and are not redistributed here. Put them beside this folder, then run from `scripts/`:

```
fit2041.py      fit the 2041 vector silhouette to the OSM boundary
classes2041.py  rasterise exact 2041 classes, compute areas
vec2041.py      export 2041 line/colony vectors
icpfit.py       fit the 1962 and 2001 scans (config in results/cfg*.json)
warp.py         warp all three sheets onto the common grid
km.py           cluster the enhanced scans
relabel.py      (only needed if the grid changes) relabel by nearest old centroid
harmonise.py    map clusters to common classes
ghsl.py         range-read GHSL epochs (no full tile download)
cross.py        cross classes with built-up
limit.py        urban limits and the 2041 green-land table
webassets.py    build the web layers
build_qgis_project.py   assemble the QGIS project (run headless via python-qgis.bat)
```

Needs `pymupdf`, `rasterio`, `geopandas`, `shapely`, `pyproj`, `opencv-python`, `scikit-learn`, `scipy`, `Pillow`. The QGIS script needs a QGIS install (built against 4.0.2).

The `.qgz` also references the aligned sheet imagery, which is excluded here; rebuild it with `warp.py` or remove those layers.

## Sources and licences

- Delhi Development Authority, Master Plan for Delhi land-use plans: 1962 (1976 reprint), 2001 (1996 reprint), Draft 2041. Not redistributed in this repository.
- European Commission JRC, **GHS-BUILT-S R2023A** — building surface, 100 m. CC BY 4.0.
- Delhi boundary © **OpenStreetMap** contributors, ODbL.
- Code in this repository: MIT (see `LICENSE`). Derived data and figures: CC BY 4.0, attribute Sahasrik Ragani.

Note on earlier files: `images/*_georef.tif` in the parent folder (from an earlier tool pass) are **not** georeferenced — each whole sheet, legend and margins included, was stretched to a bounding box. Do not use them for measurement.
