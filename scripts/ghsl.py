import rasterio, numpy as np, json
from rasterio.windows import from_bounds
from rasterio.warp import transform_bounds
import os
os.environ['GDAL_HTTP_MULTIRANGE']='YES'; os.environ['CPL_VSIL_CURL_ALLOWED_EXTENSIONS']='.zip,.tif'
B=(76.80,28.37,77.39,28.92)
out={}
for yr in range(1975,2031,5):
    name=f"GHS_BUILT_S_E{yr}_GLOBE_R2023A_54009_100_V1_0_R6_C26"
    url=f"/vsizip//vsicurl/https://jeodpp.jrc.ec.europa.eu/ftp/jrc-opendata/GHSL/GHS_BUILT_S_GLOBE_R2023A/GHS_BUILT_S_E{yr}_GLOBE_R2023A_54009_100/V1-0/tiles/{name}.zip/{name}.tif"
    with rasterio.open(url) as r:
        w=from_bounds(*transform_bounds(4326,r.crs,*B),r.transform).round_offsets().round_lengths()
        a=r.read(1,window=w); tr=r.window_transform(w)
        prof=r.profile; prof.update(height=a.shape[0],width=a.shape[1],transform=tr,compress='deflate',tiled=False,blockxsize=None,blockysize=None)
        prof.pop('blockxsize');prof.pop('blockysize')
        with rasterio.open(f'ghsl_built_{yr}.tif','w',**prof) as o: o.write(a,1)
    print(yr,a.shape,a.dtype,int(a[a<65535].sum()/1e6),'km2 built (window)',flush=True)
