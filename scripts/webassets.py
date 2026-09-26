import numpy as np, rasterio, json, cv2, pymupdf as fitz
from rasterio.transform import Affine
from rasterio.warp import reproject, Resampling
from rasterio.features import rasterize
from shapely.geometry import shape, mapping
from shapely.ops import transform as stf
from pyproj import Transformer
from PIL import Image
g=json.load(open('grid.json')); H,W=g['H'],g['W']; tr=Affine(10,0,g['x0'],0,-10,g['y1'])
T=Transformer.from_crs(4326,32643,always_xy=True)
nct=stf(lambda x,y:T.transform(x,y),shape(json.load(open('nct_nom.json'))['features'][0]['geometry']))
inside=rasterize([mapping(nct)],out_shape=(H,W),transform=tr).astype(bool)
rr,cc=np.where(inside); pad=150
r0,r1,c0,c1=max(rr.min()-pad,0),min(rr.max()+pad,H),max(cc.min()-pad,0),min(cc.max()+pad,W)
OW=1000; sc=OW/(c1-c0); OH=int(round((r1-r0)*sc))
def fit(a,interp=Image.LANCZOS):
    return Image.fromarray(a[r0:r1,c0:c1]).resize((OW,OH),interp)
ins=inside[r0:r1,c0:c1]
soft=cv2.resize(ins.astype(np.float32),(OW,OH),interpolation=cv2.INTER_AREA)
# scans: dim outside NCT
def sheet(rgb,name):
    a=rgb[r0:r1,c0:c1]; img=np.array(Image.fromarray(a).resize((OW,OH),Image.LANCZOS)).astype(np.float32)
    has=cv2.resize((a.sum(2)>0).astype(np.float32),(OW,OH),interpolation=cv2.INTER_AREA)
    alpha=(has*(0.25+0.75*soft)*255).astype(np.uint8)
    Image.fromarray(np.dstack([img.astype(np.uint8),alpha])).save(f'web/sheet_{name}.webp',quality=82)
for y in ('1962','2001'):
    sheet(np.moveaxis(rasterio.open(f'mpd{y}_scan_utm43_10m.tif').read(),0,2),y)
# 2041 sheet render + warp
p=fitz.open('C:/Users/sahas/Desktop/Temp MONSOON 2026/SPS 451/Delhi Masterplans/Delhi Master Plan 2041 Proposed Land Use.pdf')[0]
clip=fitz.Rect(0,0,2858,2300); pix=p.get_pixmap(dpi=72*2,clip=clip,alpha=False)
src=np.frombuffer(pix.samples,np.uint8).reshape(pix.height,pix.width,3)
A=np.load('A2041.npy'); s2=pix.width/clip.width
st=Affine(A[0,0]/s2,A[0,1]/s2,A[0,2],A[1,0]/s2,A[1,1]/s2,A[1,2])
out=np.zeros((3,H,W),np.uint8)
for b in range(3): reproject(src[:,:,b].copy(),out[b],src_transform=st,src_crs='EPSG:32643',dst_transform=tr,dst_crs='EPSG:32643',resampling=Resampling.bilinear)
rgb41=np.moveaxis(out,0,2); rgb41[(rgb41.sum(2)==0)]=[1,1,1]; sheet(rgb41,'2041')
with rasterio.open('mpd2041_sheet_utm43_10m.tif','w',driver='GTiff',height=H,width=W,count=3,dtype='uint8',crs='EPSG:32643',transform=tr,compress='deflate',photometric='RGB') as d: d.write(out)
# class maps
pal=np.array([[222,219,208],[242,196,36],[204,52,66],[46,112,190],[74,160,86],[176,204,126],[118,188,226]],np.uint8)
for y in ('1962','2001','2041'):
    s=rasterio.open(f'harm_{y}.tif').read(1)[r0:r1,c0:c1]
    s=np.array(Image.fromarray(s).resize((OW,OH),Image.NEAREST))
    rgba=np.zeros((OH,OW,4),np.uint8); v=s!=255; rgba[v,:3]=pal[s[v]]; rgba[v,3]=255
    Image.fromarray(rgba).save(f'web/classes_{y}.png',optimize=True)
# built-up epochs: ink alpha = fraction
B=np.load('built_grid.npz')
for y in range(1975,2031,5):
    f=B[str(y)][r0:r1,c0:c1].astype(np.float32)/255
    f=cv2.resize(f,(OW,OH),interpolation=cv2.INTER_AREA)*soft
    a=(np.clip(f*1.6,0,1)**0.8*235).astype(np.uint8)
    rgba=np.zeros((OH,OW,4),np.uint8); rgba[...,0]=26; rgba[...,1]=10; rgba[...,2]=46; rgba[...,3]=a
    Image.fromarray(rgba).save(f'web/built_{y}.png',optimize=True)
# limits outline + unauthorized colonies
for y in ('1962','2001'):
    L=rasterio.open(f'limit_{y}.tif').read(1)[r0:r1,c0:c1]
    m=cv2.resize((L==1).astype(np.uint8),(OW,OH),interpolation=cv2.INTER_NEAREST)
    cs,_=cv2.findContours(m,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)
    json.dump([c[:,0,:].tolist() for c in cs if cv2.contourArea(c)>200],open(f'web/limit_{y}.json','w'))
u=rasterio.open('mpd2041_unauth_utm43.tif')
uu=np.zeros((H,W),np.uint8); reproject(u.read(1),uu,src_transform=u.transform,src_crs=u.crs,dst_transform=tr,dst_crs='EPSG:32643',resampling=Resampling.max,src_nodata=255,dst_nodata=0)
um=cv2.resize((uu[r0:r1,c0:c1]==1).astype(np.float32),(OW,OH),interpolation=cv2.INTER_AREA)
rgba=np.zeros((OH,OW,4),np.uint8); rgba[...,0]=230; rgba[...,1]=0; rgba[...,2]=150; rgba[...,3]=(np.clip(um*1.5,0,1)*230).astype(np.uint8)
Image.fromarray(rgba).save('web/unauth_2041.png',optimize=True)
# NCT outline path
ex=np.array(nct.exterior.coords); px=(ex[:,0]-(g['x0']+c0*10))/10*sc; py=((g['y1']-r0*10)-ex[:,1])/10*sc
json.dump({'w':OW,'h':OH,'nct':[[round(a,1),round(b,1)] for a,b in zip(px,py)],'km_px':100*sc},open('web/frame.json','w'))
print(OW,OH,'px per km',100*sc)
