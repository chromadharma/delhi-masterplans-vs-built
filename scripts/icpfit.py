import json, sys, numpy as np
from shapely.geometry import shape
from shapely.ops import transform as stf
from pyproj import Transformer
from scipy.spatial import cKDTree
cfg=json.load(open(sys.argv[1])); outp=sys.argv[2]
T=Transformer.from_crs(4326,32643,always_xy=True)
nct=stf(lambda x,y:T.transform(x,y),shape(json.load(open('nct_nom.json'))['features'][0]['geometry']))
ex=nct.exterior; B=np.array([ex.interpolate(d).coords[0] for d in np.arange(0,ex.length,50)]); tree=cKDTree(B)
L=cfg['gcps']; lp=np.array([g['px'] for g in L],float); lu=np.array([T.transform(*g['lonlat']) for g in L])
# densify traced polylines
tr=[]
for seg in cfg.get('boundary',[]):
    s=np.array(seg,float)
    for a,b in zip(s[:-1],s[1:]):
        n=max(2,int(np.hypot(*(b-a))/10)); tr+=list(a+(b-a)*np.linspace(0,1,n,endpoint=False)[:,None])
tr=np.array(tr) if tr else np.zeros((0,2))
def D(P): return np.c_[P,np.ones(len(P))]
# init from landmarks (affine if >=3)
A,*_=np.linalg.lstsq(D(lp),lu,rcond=None)
w=cfg.get('landmark_weight',20)
for it in range(100):
    if len(tr)==0: break
    q=D(tr)@A; d,idx=tree.query(q); keep=d<max(np.quantile(d,0.9),1)
    src=np.r_[D(tr[keep]), np.repeat(D(lp),w,0)]; dst=np.r_[B[idx[keep]], np.repeat(lu,w,0)]
    A,*_=np.linalg.lstsq(src,dst,rcond=None)
q=D(tr)@A; d,_=tree.query(q) if len(tr) else (np.array([0]),None)
lr=np.hypot(*(D(lp)@A-lu).T)
M=A[:2].T
print('boundary dist m median',round(float(np.median(d))),'p90',round(float(np.quantile(d,.9))))
print('landmark resid m',[(g['name'],round(r)) for g,r in zip(L,lr)])
print('m/px x,y',np.linalg.norm(M[:,0]),np.linalg.norm(M[:,1]),'rot',np.degrees(np.arctan2(M[1,0],M[0,0])))
# independent check points
for c in cfg.get('checks',[]):
    u=np.array(T.transform(*c['lonlat'])); print('CHECK',c['name'],round(np.hypot(*(D(np.array([c['px']],float))@A-u)[0])),'m')
json.dump({'A':A.T.tolist()},open(outp,'w'))
