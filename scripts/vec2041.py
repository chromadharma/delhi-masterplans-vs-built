import pymupdf as fitz, numpy as np, geopandas as gpd
from shapely.geometry import LineString, Polygon, MultiLineString
p=fitz.open('C:/Users/sahas/Desktop/Temp MONSOON 2026/SPS 451/Delhi Masterplans/Delhi Master Plan 2041 Proposed Land Use.pdf')[0]
A=np.load('A2041.npy')
def tf(pt): return (A[0,0]*pt.x+A[0,1]*pt.y+A[0,2], A[1,0]*pt.x+A[1,1]*pt.y+A[1,2])
def bez(p0,p1,p2,p3,n=8):
    t=np.linspace(0,1,n)[:,None]; P=[np.array([q.x,q.y]) for q in (p0,p1,p2,p3)]
    return ((1-t)**3*P[0]+3*(1-t)**2*t*P[1]+3*(1-t)*t**2*P[2]+t**3*P[3])
def paths(x):
    segs=[]; cur=[]
    for it in x['items']:
        if it[0]=='l':
            a,b=tf(it[1]),tf(it[2])
            if cur and np.hypot(cur[-1][0]-a[0],cur[-1][1]-a[1])<1e-3: cur.append(b)
            else:
                if len(cur)>1: segs.append(cur)
                cur=[a,b]
        elif it[0]=='c':
            pts=[ (A[0,0]*q[0]+A[0,1]*q[1]+A[0,2], A[1,0]*q[0]+A[1,1]*q[1]+A[1,2]) for q in bez(*it[1:5])]
            if cur and np.hypot(cur[-1][0]-pts[0][0],cur[-1][1]-pts[0][1])<1e-3: cur+=pts[1:]
            else:
                if len(cur)>1: segs.append(cur)
                cur=pts
        elif it[0]=='re':
            r=it[1]; q=[tf(fitz.Point(r.x0,r.y0)),tf(fitz.Point(r.x1,r.y0)),tf(fitz.Point(r.x1,r.y1)),tf(fitz.Point(r.x0,r.y1)),tf(fitz.Point(r.x0,r.y0))]
            segs.append(q)
    if len(cur)>1: segs.append(cur)
    return segs
LAY={'planning_zone_boundary':((0.0,0.149,0.451),2.0),'rail_black_white':((0.0,0.0,0.0),2.0),'transit_red_dashed':((0.902,0.0,0.0),1.0),'transit_grey_casing':((0.8,0.8,0.8),2.0),'transit_purple':((0.773,0.0,1.0),1.2),'transit_orange':((0.659,0.439,0.0),1.2),'yamuna_blue_outline':((0.0,0.361,0.902),1.0)}
rows=[]
for x in p.get_drawings():
    if x['type']!='s' or not x['color'] or x['rect'].x0>2850 or x['rect'].y1>2300: continue
    k=(tuple(round(v,3) for v in x['color']),round(x['width'] or 0,2))
    for name,v in LAY.items():
        if k==v:
            for s in paths(x): rows.append((name,LineString(s)))
    if k==((0.902,0.0,0.663),0.12):
        for s in paths(x):
            if len(s)>=4:
                pg=Polygon(s)
                if pg.is_valid and pg.area>0: rows.append(('unauthorized_colony',pg))
g=gpd.GeoDataFrame({'layer':[r[0] for r in rows]},geometry=[r[1] for r in rows],crs=32643)
for name,sub in g.groupby('layer'):
    sub.to_file('mpd2041_vectors.gpkg',layer=name,driver='GPKG')
    print(name,len(sub), round(sub.length.sum()/1000,1) if sub.geom_type.iloc[0]=='LineString' else round(sub.unary_union.area/1e6,1))
