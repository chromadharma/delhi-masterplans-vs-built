import rasterio, numpy as np, cv2
from scipy.spatial import cKDTree
def enh(a):
    bgr=cv2.cvtColor(a,cv2.COLOR_RGB2BGR); m=cv2.medianBlur(bgr,7)
    hsv=cv2.cvtColor(m,cv2.COLOR_BGR2HSV).astype(np.float32); hsv[:,:,1]=np.clip((hsv[:,:,1]-20)*1.8,0,255)
    e=cv2.cvtColor(hsv.astype(np.uint8),cv2.COLOR_HSV2BGR); lab=cv2.cvtColor(e,cv2.COLOR_BGR2LAB)
    lab[:,:,0]=cv2.createCLAHE(2.0,(16,16)).apply(lab[:,:,0]); return lab
for yr in ('2001','1962'):
    a=np.moveaxis(rasterio.open(f'mpd{yr}_scan_utm43_10m.tif').read(),0,2); valid=a.sum(2)>0
    lab=enh(a).astype(np.float32)
    old=np.load(f'km{yr}_old.npy')[:5500,:3600]; R0,C0=100,1700; h,w=old.shape
    sub=lab[R0:R0+h,C0:C0+w]; K=old[old!=255].max()+1
    cen=np.array([sub[old==k].mean(0) for k in range(K)])
    new=np.full(valid.shape,255,np.uint8)
    _,idx=cKDTree(cen).query(lab[valid]); new[valid]=idx
    reg=new[R0:R0+h,C0:C0+w]; m=old!=255
    print(yr,'agreement with old labels in old region',round((reg[m]==old[m]).mean(),4))
    np.save(f'km{yr}.npy',new)
