import rasterio, numpy as np, json, cv2
from rasterio.transform import Affine
from rasterio.warp import reproject, Resampling
from PIL import Image; Image.MAX_IMAGE_PIXELS=None
IMG="C:/Users/sahas/Desktop/Temp MONSOON 2026/SPS 451/Delhi Masterplans/images/"
x0,y1=678000,3198000; x1,y0=731000,3142000; res=10
W=(x1-x0)//res; H=(y1-y0)//res
dst_tr=Affine(res,0,x0,0,-res,y1)
json.dump({'x0':x0,'y1':y1,'W':W,'H':H,'res':res},open('grid.json','w'))
for yr,Af in [('1962','A1962b.json'),('2001','A2001.json')]:
    A=np.array(json.load(open(Af))['A'])
    src=np.array(Image.open(IMG+f'{yr}_map.png').convert('RGB'))
    # mask legend/margins: keep only left part of sheet
    src_tr=Affine(A[0,0],A[0,1],A[0,2],A[1,0],A[1,1],A[1,2])
    out=np.zeros((3,H,W),np.uint8)
    for b in range(3):
        reproject(src[:,:,b],out[b],src_transform=src_tr,src_crs='EPSG:32643',dst_transform=dst_tr,dst_crs='EPSG:32643',resampling=Resampling.bilinear,src_nodata=None,dst_nodata=0)
    prof=dict(driver='GTiff',height=H,width=W,count=3,dtype='uint8',crs='EPSG:32643',transform=dst_tr,compress='deflate',photometric='RGB')
    with rasterio.open(f'mpd{yr}_scan_utm43_10m.tif','w',**prof) as d: d.write(out)
    # also native-res georeferenced (rotated geotransform) for QGIS
    prof2=dict(driver='GTiff',height=src.shape[0],width=src.shape[1],count=3,dtype='uint8',crs='EPSG:32643',transform=src_tr,compress='deflate',photometric='RGB')
    with rasterio.open(f'mpd{yr}_scan_georef_native.tif','w',**prof2) as d: d.write(np.moveaxis(src,2,0))
    Image.fromarray(np.moveaxis(out,0,2)).resize((W//5,H//5)).save(f'warp{yr}.jpg')
# 2041 classes to grid
with rasterio.open('mpd2041_classes_utm43.tif') as s:
    c=np.full((H,W),255,np.uint8)
    reproject(s.read(1),c,src_transform=s.transform,src_crs=s.crs,dst_transform=dst_tr,dst_crs='EPSG:32643',resampling=Resampling.mode,src_nodata=255,dst_nodata=255)
prof=dict(driver='GTiff',height=H,width=W,count=1,dtype='uint8',crs='EPSG:32643',transform=dst_tr,compress='deflate',nodata=255)
with rasterio.open('mpd2041_classes_10m.tif','w',**prof) as d: d.write(c,1)
print(W,H)
