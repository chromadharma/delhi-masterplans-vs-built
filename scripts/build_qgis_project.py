import os, sys
from qgis.core import *
from qgis.PyQt.QtGui import QColor
D=r"C:/Users/sahas/Desktop/Temp MONSOON 2026/SPS 451/Delhi Masterplans/analysis"
app=QgsApplication([],False); app.initQgis()
P=QgsProject.instance(); P.setCrs(QgsCoordinateReferenceSystem("EPSG:32643"))
P.setTitle("Delhi master plans aligned (1962, 2001, 2041 draft) vs GHSL built-up")
md=P.metadata(); md.setAuthor("Sahasrik Ragani"); md.setAbstract("Aligned MPD sheets, common land-use classes, urban limits and GHSL built-surface 1975–2030. Analysis by Sahasrik Ragani, Sept 2026."); P.setMetadata(md)
root=P.layerTreeRoot()
def rl(path,name,group,visible=True):
    l=QgsRasterLayer(path,name)
    assert l.isValid(), path
    P.addMapLayer(l,False); n=group.addLayer(l); n.setItemVisibilityChecked(visible); return l
def vl(path,name,group,visible=True):
    l=QgsVectorLayer(path,name,"ogr"); assert l.isValid(), path
    P.addMapLayer(l,False); n=group.addLayer(l); n.setItemVisibilityChecked(visible); return l
def paletted(l,items):
    cls=[QgsPalettedRasterRenderer.Class(v,QColor(c),lab) for v,c,lab in items]
    l.setRenderer(QgsPalettedRasterRenderer(l.dataProvider(),1,cls)); l.triggerRepaint()
def line(l,color,w,dash=False):
    sym=QgsLineSymbol.createSimple({'color':color,'width':str(w),'line_style':'dash' if dash else 'solid'}); l.renderer().setSymbol(sym)
HARM=[(0,'#DEDBD0','Uncoloured (rural, transport, hatched)'),(1,'#F2C424','Residential'),(2,'#CC3442','Commercial & industrial'),(3,'#2E70BE','Public, semi-public & govt'),(4,'#4AA056','Parks & recreation'),(5,'#B0CC7E','Green belt & agriculture'),(6,'#76BCE2','Water & floodplain')]
g0=root.addGroup("Reference")
nct=vl(D+"/vectors/nct_boundary_osm.geojson","NCT boundary (OSM)",g0)
nct.renderer().setSymbol(QgsFillSymbol.createSimple({'color':'0,0,0,0','outline_color':'#15201F','outline_width':'0.6','outline_style':'dash'}))
g1=root.addGroup("GHSL built surface (fraction of 100 m cell)")
for y in range(2030,1974,-5):
    l=rl(D+f"/ghsl/ghsl_built_{y}.tif",f"GHSL built {y}"+(" (projection)" if y>2020 else ""),g1,visible=(y==2020))
    sh=QgsRasterShader(); f=QgsColorRampShader(); f.setColorRampType(QgsColorRampShader.Interpolated)
    f.setColorRampItemList([QgsColorRampShader.ColorRampItem(0,QColor(0,0,0,0),'0'),QgsColorRampShader.ColorRampItem(500,QColor(68,1,84,90),'5%'),QgsColorRampShader.ColorRampItem(3000,QColor(59,82,139,200),'30%'),QgsColorRampShader.ColorRampItem(6000,QColor(33,145,140,230),'60%'),QgsColorRampShader.ColorRampItem(10000,QColor(253,231,37,255),'100%')])
    sh.setRasterShaderFunction(f); r=QgsSingleBandPseudoColorRenderer(l.dataProvider(),1,sh); l.setRenderer(r)
    l.dataProvider().setNoDataValue(1,65535)
g1.setExpanded(False)
g2=root.addGroup("Draft MPD 2041")
v=D+"/vectors/mpd2041_vectors.gpkg"
for lay,name,col,w,vis in [("planning_zone_boundary","Planning zone boundaries","#002673",0.5,False),("rail_black_white","Rail","#000000",0.6,False),("transit_red_dashed","Transit (red dashed, likely MRTS)","#E60000",0.4,False),("transit_purple","Transit (purple)","#C500FF",0.5,False),("transit_orange","Transit (orange)","#A87000",0.5,False)]:
    l=vl(v+f"|layername={lay}",name,g2,vis); line(l,col,w)
u=vl(v+"|layername=unauthorized_colony","Unauthorized colonies (as mapped)",g2,False)
u.renderer().setSymbol(QgsFillSymbol.createSimple({'color':'230,0,150,110','outline_color':'#E60096','outline_width':'0.2'}))
c41=rl(D+"/rasters/mpd2041_classes_utm43.tif","2041 exact classes (from PDF vectors)",g2,False)
paletted(c41,[(0,'#FFFFFF','Uncoloured / land pooling / transport'),(1,'#FFFF00','Residential'),(2,'#FF0000','Commercial'),(3,'#A900E6','Industrial'),(4,'#4CE600','City parks & green buffers'),(5,'#267300','Regional park'),(6,'#0070FF','Public & semi-public'),(7,'#B2B2B2','Government'),(8,'#ABCD66','Green belt'),(9,'#BEE8FF','River, floodplain & drains'),(10,'#004D7F','Facility corridor')])
h41=rl(D+"/rasters/harm_2041.tif","2041 common classes",g2,False); paletted(h41,HARM)
rl(D+"/rasters/mpd2041_sheet_utm43_10m.tif","2041 sheet (aligned)",g2,True)
for yr,label in [("2001","MPD 2001 (1996 reprint)"),("1962","MPD 1962 (1976 reprint)")]:
    g=root.addGroup(label)
    lim=rl(D+f"/rasters/limit_{yr}.tif",f"{yr} urban limit (1 inside, 2 >=400 m outside)",g,False)
    paletted(lim,[(0,'#BBBBBB','400 m exclusion ring'),(1,'#F2C42480','Inside urban limit'),(2,'#3B528B80','>=400 m outside')])
    lim.renderer().setOpacity(0.55)
    h=rl(D+f"/rasters/harm_{yr}.tif",f"{yr} common classes",g,False); paletted(h,HARM)
    rl(D+f"/rasters/mpd{yr}_scan_georef_native.tif",f"{yr} scan (native res, affine fit)",g,False)
    g.setItemVisibilityChecked(False)
xyz=QgsRasterLayer("type=xyz&url=https://mt1.google.com/vt/lyrs%3Dy%26x%3D%7Bx%7D%26y%3D%7By%7D%26z%3D%7Bz%7D&zmax=20&zmin=0","Google Hybrid (basemap)","wms")
if xyz.isValid(): P.addMapLayer(xyz,False); gb=root.addGroup("Basemap"); gb.addLayer(xyz).setItemVisibilityChecked(False)
ext=nct.extent(); 
P.viewSettings().setDefaultViewExtent(QgsReferencedRectangle(QgsCoordinateTransform(nct.crs(),P.crs(),P).transformBoundingBox(ext),P.crs()))
out=D+"/Delhi_Masterplans_aligned.qgz"
print("saved",P.write(out),out)
app.exitQgis()
