import pymupdf as fitz, numpy as np, json, cv2, rasterio
from rasterio.transform import Affine
from rasterio.features import rasterize
from shapely.geometry import shape, mapping
from shapely.ops import transform as stf
from pyproj import Transformer
SRC="C:/Users/sahas/Desktop/Temp MONSOON 2026/SPS 451/Delhi Masterplans/Delhi Master Plan 2041 Proposed Land Use.pdf"
p=fitz.open(SRC)[0]; dr=p.get_drawings()
A=np.load('A2041.npy')
CLS={(1.0,1.0,0.0):1,(1.0,0.0,0.0):2,(0.663,0.0,0.902):3,(0.518,0.0,0.659):3,(0.298,0.902,0.0):4,(0.149,0.451,0.0):5,(0.0,0.439,1.0):6,(0.698,0.698,0.698):7,(0.671,0.804,0.4):8,(0.745,0.91,1.0):9,(0.631,0.824,0.91):9,(0.0,0.302,0.498):10,(0.0,0.773,1.0):9,(1.0,1.0,1.0):0}
NAMES={1:'Residential',2:'Commercial',3:'Industrial',4:'City parks & green buffers',5:'Regional park (Ridge)',6:'Public & semi-public',7:'Government',8:'Green belt',9:'Water, drains & floodplain',10:'Facility corridor',0:'Uncoloured: land pooling, transport, villages, roads'}
def draw(sh,x):
    for it in x['items']:
        if it[0]=='l': sh.draw_line(it[1],it[2])
        elif it[0]=='re': sh.draw_rect(it[1])
        elif it[0]=='qu': sh.draw_quad(it[1])
        elif it[0]=='c': sh.draw_bezier(it[1],it[2],it[3],it[4])
out=fitz.open(); op=out.new_page(width=p.rect.width,height=p.rect.height); sh=op.new_shape()
for x in dr:
    if x['type'] not in('f','fs') or x['rect'].x0>2850 or x['rect'].y0>2300: continue
    k=CLS[tuple(round(v,3) for v in x['fill'])]
    draw(sh,x); sh.finish(fill=(k/255,0,0),color=None,even_odd=x.get('even_odd',False),closePath=True)
sh.commit()
fitz.TOOLS.set_aa_level(0)
DPI=144; sc=DPI/72
PIXC=op.get_pixmap(dpi=DPI,alpha=False)
up=fitz.open().new_page(width=p.rect.width,height=p.rect.height); su=up.new_shape()
for x in dr:
    if x['type']=='s' and x['color'] and tuple(round(v,3) for v in x['color'])==(0.902,0.0,0.663) and x['rect'].x0<2850:
        draw(su,x); su.finish(fill=(1,0,0),color=None,closePath=True)
su.commit()
cls=np.frombuffer(PIXC.samples,np.uint8)
W=PIXC.width; H=PIXC.height
cls=cls.reshape(H,W,3)
white=(cls==255).all(2); cls=cls[:,:,0].copy(); cls[white]=0
PU=up.get_pixmap(dpi=DPI,alpha=False); un=np.frombuffer(PU.samples,np.uint8).reshape(PU.height,PU.width,3)[:H,:W]
un=(un[:,:,1]==0)
# pixel -> UTM: pt = px/sc
Apx=A.copy(); Apx[:,:2]/=sc
tr=Affine(Apx[0,0],Apx[0,1],Apx[0,2],Apx[1,0],Apx[1,1],Apx[1,2])
g=json.load(open('nct_nom.json'))['features'][0]['geometry']
T=Transformer.from_crs(4326,32643,always_xy=True)
poly=stf(lambda x,y:T.transform(x,y),shape(g))
inside=rasterize([mapping(poly)],out_shape=(H,W),transform=tr).astype(bool)
pa=abs(Apx[0,0]*Apx[1,1]-Apx[0,1]*Apx[1,0])/1e6
res={}
tot=inside.sum()*pa
print('NCT (raster) km2',tot, 'pixel m', np.sqrt(pa*1e6))
for k in sorted(NAMES):
    a=((cls==k)&inside).sum()*pa; res[NAMES[k]]=round(a,1); print(f'{NAMES[k]:55s} {a:8.1f} km2 {100*a/tot:5.1f}%')
print('outside-NCT coloured km2', ((cls>0)&~inside).sum()*pa)
ua=(un&inside).sum()*pa
print('Unauthorized colonies overlay km2',ua)
for k in sorted(NAMES):
    print('  unauth on',NAMES[k], round((un&inside&(cls==k)).sum()*pa,1))
prof=dict(driver='GTiff',height=H,width=W,count=1,dtype='uint8',crs='EPSG:32643',transform=tr,compress='deflate',nodata=255)
c2=cls.copy(); c2[~inside]=255
with rasterio.open('mpd2041_classes_utm43.tif','w',**prof) as d: d.write(c2,1)
with rasterio.open('mpd2041_unauth_utm43.tif','w',**prof) as d: d.write(np.where(inside,un,255).astype(np.uint8),1)
json.dump({'areas_km2':res,'nct_km2':tot,'unauth_km2':ua,'unauth_by_class':{NAMES[k]:round((un&inside&(cls==k)).sum()*pa,1) for k in NAMES}},open('areas2041.json','w'),indent=1)
