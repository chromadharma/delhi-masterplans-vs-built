import numpy as np, rasterio, json, cv2
from scipy import ndimage as ndi
from rasterio.transform import Affine
g=json.load(open('grid.json')); H,W=g['H'],g['W']; tr=Affine(10,0,g['x0'],0,-10,g['y1'])
B=np.load('built_grid.npz'); yrs=list(range(1975,2031,5))
built={y:B[str(y)].astype(np.float32)/255 for y in yrs}
plans={y:rasterio.open(f'harm_{y}.tif').read(1) for y in ('1962','2001','2041')}
disk=lambda r: cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(2*r+1,2*r+1))
out={'epochs':yrs}
prof=dict(driver='GTiff',height=H,width=W,count=1,dtype='uint8',crs='EPSG:32643',transform=tr,compress='deflate',nodata=255)
for p in ('1962','2001'):
    s=plans[p]; cov=s!=255
    u=(np.isin(s,[1,2,3,4])|np.load(f'hatch_{p}.npy')).astype(np.uint8)
    lim=cv2.morphologyEx(u,cv2.MORPH_CLOSE,disk(40))
    lim=ndi.binary_fill_holes(lim)
    lab,n=ndi.label(lim); sizes=ndi.sum(lim,lab,range(1,n+1)); keep=np.isin(lab,1+np.where(sizes>5e5)[0])  # >50 km2 blobs
    lim=keep&cov
    outside=cov&~cv2.dilate(lim.astype(np.uint8),disk(40)).astype(bool)
    r={'limit_km2':round(lim.sum()*1e-4,1),'outside_km2':round(outside.sum()*1e-4,1),
       'inside_built':[round(float(built[y][lim].sum()*1e-4),1) for y in yrs],
       'outside_built':[round(float(built[y][outside].sum()*1e-4),1) for y in yrs],
       'outside_urbanised_km2':[round(float((built[y][outside]>=0.2).sum()*1e-4),1) for y in yrs],
       'inside_urbanised_km2':[round(float((built[y][lim]>=0.2).sum()*1e-4),1) for y in yrs]}
    out[p]=r
    L=np.full((H,W),255,np.uint8); L[cov]=0; L[lim]=1; L[outside]=2
    with rasterio.open(f'limit_{p}.tif','w',**prof) as d: d.write(L,1)
    print(p,{k:v for k,v in r.items()})
s=plans['2041']; c41=rasterio.open('mpd2041_classes_10m.tif').read(1)
r={}
for name,cls in [('Green belt',[8]),('Regional park (Ridge)',[5]),('River, floodplain & drains',[9]),('City parks & green buffers',[4])]:
    m=np.isin(c41,cls); e=cv2.erode(m.astype(np.uint8),disk(10)).astype(bool)
    r[name]={'area_km2':round(m.sum()*1e-4,1),'core_km2':round(e.sum()*1e-4,1),
      'core_built_surface_km2':[round(float(built[y][e].sum()*1e-4),2) for y in yrs],
      'core_urbanised_km2':[round(float((built[y][e]>=0.2).sum()*1e-4),1) for y in yrs]}
    print(name,r[name]['area_km2'],r[name]['core_km2'],'urbanised 1975',r[name]['core_urbanised_km2'][0],'2000',r[name]['core_urbanised_km2'][5],'2020',r[name]['core_urbanised_km2'][9],'2030proj',r[name]['core_urbanised_km2'][11])
out['2041_green']=r
json.dump(out,open('limit.json','w'),indent=1)
