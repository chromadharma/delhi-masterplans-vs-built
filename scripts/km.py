import rasterio, numpy as np, cv2, sys
from sklearn.cluster import MiniBatchKMeans
from PIL import Image, ImageDraw
yr=sys.argv[1]; K=int(sys.argv[2])
a=np.moveaxis(rasterio.open(f'mpd{yr}_scan_utm43_10m.tif').read(),0,2)
valid=a.sum(2)>0
bgr=cv2.cvtColor(a,cv2.COLOR_RGB2BGR)
# enhancement: median to suppress hatch/stipple, then boost saturation and local contrast
m=cv2.medianBlur(bgr,7)
hsv=cv2.cvtColor(m,cv2.COLOR_BGR2HSV).astype(np.float32)
hsv[:,:,1]=np.clip((hsv[:,:,1]-20)*1.8,0,255)
e=cv2.cvtColor(hsv.astype(np.uint8),cv2.COLOR_HSV2BGR)
lab=cv2.cvtColor(e,cv2.COLOR_BGR2LAB)
l=lab[:,:,0]; lab[:,:,0]=cv2.createCLAHE(2.0,(16,16)).apply(l)
X=lab[valid].astype(np.float32)
km=MiniBatchKMeans(K,random_state=0,batch_size=20000,n_init=5).fit(X[np.random.default_rng(0).choice(len(X),400000,replace=False)])
lab_img=np.full(valid.shape,255,np.uint8); lab_img[valid]=km.predict(X)
np.save(f'km{yr}.npy',lab_img)
cen=cv2.cvtColor(km.cluster_centers_.clip(0,255).astype(np.uint8)[None],cv2.COLOR_LAB2RGB)[0]
# medoid-ish swatch: mean original RGB per cluster
sw=[a[lab_img==k].mean(0).astype(int) for k in range(K)]
cnt=[(lab_img==k).sum()*1e-4 for k in range(K)]
# contact sheet: for each cluster, show original crop highlighting cluster in magenta over a small area
H,W=valid.shape; cs=Image.new('RGB',(K*120,260),'white'); d=ImageDraw.Draw(cs)
sub=Image.fromarray(a[::4,::4])
for k in range(K):
    d.rectangle([k*120+10,10,k*120+110,60],fill=tuple(sw[k])); d.text((k*120+10,65),f'{k}: {cnt[k]:.0f}km2',fill='black')
cs.save(f'km{yr}_sw.png')
for k in range(K):
    ov=a[::4,::4].copy(); mk=lab_img[::4,::4]==k; ov[mk]=[255,0,255]
    Image.fromarray(ov).resize((W//10,H//10)).save(f'km{yr}_c{k:02d}.png')
print([ (k,tuple(sw[k]),round(cnt[k],1)) for k in range(K)])
