import json, numpy as np, cv2
from shapely.geometry import shape
from shapely.ops import transform
from pyproj import Transformer
from scipy.spatial import cKDTree
g=json.load(open('nct_nom.json'))['features'][0]['geometry']
T=Transformer.from_crs(4326,32643,always_xy=True)
poly=transform(lambda x,y: T.transform(x,y), shape(g))
print('NCT area km2', poly.area/1e6)
B=np.array(poly.exterior.coords); 
# densify
bl=poly.exterior; B=np.array([bl.interpolate(d).coords[0] for d in np.arange(0,bl.length,100)])
im=cv2.imread('fills2041_36.png'); m=(im.sum(2)<750).astype(np.uint8)*255
m=cv2.morphologyEx(m,cv2.MORPH_CLOSE,np.ones((25,25),np.uint8))
cs,_=cv2.findContours(m,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_NONE)
c=max(cs,key=cv2.contourArea)[:,0,:].astype(float)
print('silhouette px area', cv2.contourArea(c.astype(np.float32)), 'as km2 via scalebar', cv2.contourArea(c.astype(np.float32))/(20.25**2))
# px -> pt: /0.5 ; page pt coords
P=c/0.5
# initial: 40.5 pt/km, flip y
s=1000/40.5
init=np.array([[s,0,0],[0,-s,0]])
X0=P@init[:,:2].T
init[:,2]=np.array(poly.centroid.coords[0])-X0.mean(0)  # rough centroid
tree=cKDTree(B)
A=init.copy()
def apply(A,P): return P@A[:,:2].T+A[:,2]
for it in range(200):
    Q=apply(A,P); d,idx=tree.query(Q)
    keep=d<np.quantile(d,0.8)
    src=np.c_[P[keep],np.ones(keep.sum())]; dst=B[idx[keep]]
    sol,*_=np.linalg.lstsq(src,dst,rcond=None); A=sol.T
Q=apply(A,P); d,_=tree.query(Q)
print('affine', A); print('median resid m',np.median(d),'p80',np.quantile(d,.8),'p95',np.quantile(d,.95))
sx=np.linalg.norm(A[:,0]); sy=np.linalg.norm(A[:,1])
print('m per pt x,y', sx, sy, ' scalebar says', s, ' shear/rot deg', np.degrees(np.arctan2(A[1,0],A[0,0])), np.degrees(np.arctan2(-A[0,1],-A[1,1])))
np.save('A2041.npy',A); np.save('sil2041.npy',Q)
json.dump({'A':A.tolist()},open('A2041.json','w'))
