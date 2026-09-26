import numpy as np, rasterio, cv2, json, geopandas as gpd
from scipy import ndimage as ndi
from rasterio.features import rasterize
from shapely.geometry import shape, mapping
from shapely.ops import transform as stf
from pyproj import Transformer
g=json.load(open('grid.json')); H,W=g['H'],g['W']
from rasterio.transform import Affine
tr=Affine(10,0,g['x0'],0,-10,g['y1'])
T=Transformer.from_crs(4326,32643,always_xy=True)
nct=stf(lambda x,y:T.transform(x,y),shape(json.load(open('nct_nom.json'))['features'][0]['geometry']))
inside=rasterize([mapping(nct)],out_shape=(H,W),transform=tr).astype(bool)
# Yamuna corridor from 2041 water class + blue outline, buffered 300 m
c41=rasterio.open('mpd2041_classes_10m.tif').read(1)
yv=gpd.read_file('mpd2041_vectors.gpkg',layer='yamuna_blue_outline').union_all().buffer(400)
yam=rasterize([mapping(yv)],out_shape=(H,W),transform=tr).astype(bool) | cv2.dilate((c41==9).astype(np.uint8),np.ones((41,41),np.uint8)).astype(bool)
LINE=254
def opened(m,k): return cv2.morphologyEx(m.astype(np.uint8),cv2.MORPH_OPEN,np.ones((k,k),np.uint8)).astype(bool)
def finish(out,valid,name):
    lm=out==LINE
    idx=ndi.distance_transform_edt(lm,return_distances=False,return_indices=True)
    f=out[idx[0],idx[1]]
    # mode filter 5x5 via one-hot
    K=7; acc=np.zeros((K,H,W),np.float32)
    for c in range(K): acc[c]=cv2.boxFilter((f==c).astype(np.float32),-1,(5,5))
    s=acc.argmax(0).astype(np.uint8)
    s[~valid]=255; s[~inside]=255
    prof=dict(driver='GTiff',height=H,width=W,count=1,dtype='uint8',crs='EPSG:32643',transform=tr,compress='deflate',nodata=255)
    with rasterio.open(f'harm_{name}.tif','w',**prof) as d: d.write(s,1)
    return s
res={}
# 1962
k=np.load('km1962.npy'); a=rasterio.open('mpd1962_scan_utm43_10m.tif').read(); valid=a.sum(0)>0
o=np.full((H,W),LINE,np.uint8)
for c in (3,7,9,13,12): o[k==c]=1
o[(k==4)]=LINE; o[opened(k==4,5)]=2
o[np.isin(k,(6,8,14))]=4
o[k==1]=5
gb=np.isin(k,(5,11,17)); o[opened(gb,5)]=5
o[(k==10)&yam]=6; o[(k==10)&~yam]=3
o[opened(k==2,7)&yam]=6; o[opened(k==2,7)&~yam]=0
o[np.isin(k,(0,15,16))]=0
res['1962']=finish(o,valid,'1962')
# 2001
k=np.load('km2001.npy'); a=rasterio.open('mpd2001_scan_utm43_10m.tif').read(); valid=a.sum(0)>0
o=np.full((H,W),LINE,np.uint8)
o[np.isin(k,(4,13))]=1
o[k==6]=2; o[opened(k==10,5)]=2
o[np.isin(k,(2,5))]=3
o[np.isin(k,(3,9,15))]=4
blue=(a[2].astype(int)>a[0].astype(int)+15)
o[(k==7)&blue&yam]=6
o[np.isin(k,(0,8,12))]=0
res['2001']=finish(o,valid,'2001')
# 2041 (exact)
m={1:1,2:2,3:2,6:3,7:3,10:3,4:4,5:4,8:5,9:6,0:0}
o=np.full((H,W),255,np.uint8)
for s_,d_ in m.items(): o[c41==s_]=d_
o[~inside]=255
prof=dict(driver='GTiff',height=H,width=W,count=1,dtype='uint8',crs='EPSG:32643',transform=tr,compress='deflate',nodata=255)
with rasterio.open('harm_2041.tif','w',**prof) as d: d.write(o,1)
res['2041']=o
NAMES=['Uncoloured (rural, transport, hatched uses)','Residential','Commercial & industrial','Public, semi-public & government','Parks & recreation','Green belt & agriculture','Water & floodplain']
table={}
for yr,s in res.items():
    cov=(s!=255).sum()*1e-4
    table[yr]={'coverage_km2':round(cov,1),**{NAMES[c]:round((s==c).sum()*1e-4,1) for c in range(7)}}
    print(yr,table[yr])
json.dump(table,open('harm_areas.json','w'),indent=1)
from PIL import Image
pal=np.array([[235,232,222],[245,200,40],[200,40,60],[40,110,190],[70,160,70],[170,200,120],[120,190,230]],np.uint8)
row=[]
for yr in ('1962','2001','2041'):
    s=res[yr]; img=np.full((H,W,3),255,np.uint8); v=s!=255; img[v]=pal[s[v]]
    row.append(Image.fromarray(img).resize((W//6,H//6),Image.NEAREST))
Wd=Image.new('RGB',(3*W//6,H//6),'white')
for i,im in enumerate(row): Wd.paste(im,(i*W//6,0))
Wd.save('harm_preview.png')
