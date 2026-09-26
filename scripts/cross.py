import numpy as np, rasterio, json
from rasterio.warp import reproject, Resampling
from rasterio.transform import Affine
g=json.load(open('grid.json')); H,W=g['H'],g['W']; tr=Affine(10,0,g['x0'],0,-10,g['y1'])
plans={y:rasterio.open(f'harm_{y}.tif').read(1) for y in ('1962','2001','2041')}
nct=plans['2041']!=255
N=['Uncoloured','Residential','Commercial & industrial','Public & semi-public','Parks & recreation','Green belt & agriculture','Water & floodplain']
yrs=list(range(1975,2031,5)); built={}
for yr in yrs:
    with rasterio.open(f'ghsl_built_{yr}.tif') as s:
        a=s.read(1).astype(np.float32); a[a>10000]=0
        f=np.zeros((H,W),np.float32)
        reproject(a/10000,f,src_transform=s.transform,src_crs=s.crs,dst_transform=tr,dst_crs='EPSG:32643',resampling=Resampling.nearest)
    built[yr]=f
res={'epochs':yrs,'nct_built_km2':[round(float((built[y]*nct).sum()*1e-4),1) for y in yrs],'plans':{}}
for p,s in plans.items():
    d={}
    for c in range(7):
        m=s==c; d[N[c]]={'area_km2':round(m.sum()*1e-4,1),'built_km2':[round(float(built[y][m].sum()*1e-4),1) for y in yrs]}
    cov=s!=255
    d['_coverage_km2']=round(cov.sum()*1e-4,1)
    d['_built_in_coverage_km2']=[round(float(built[y][cov].sum()*1e-4),1) for y in yrs]
    res['plans'][p]=d
json.dump(res,open('cross.json','w'),indent=1)
print('NCT built',dict(zip(yrs,res['nct_built_km2'])))
for p in plans:
    print('\n==',p)
    for c in N:
        v=res['plans'][p][c]; print(f"  {c:28s} {v['area_km2']:7.1f}  built1975 {v['built_km2'][0]:6.1f} 2000 {v['built_km2'][5]:6.1f} 2020 {v['built_km2'][9]:6.1f}")
# save GHSL on grid for 1975..2020 as small preview arrays for web
np.savez_compressed('built_grid.npz',**{str(y):(built[y]*255).astype(np.uint8) for y in yrs})
