# -*- coding: utf-8 -*-
"""
Created on Mon Apr 12 15:04:43 2021

@author: Will Wiskes
"""
import arcpy, os, sys, time
from arcpy.sa import *
from arcpy import management as DM
from arcgis.gis import GIS
from arcpy import analysis as AN
from arcpy import conversion as CO
from arcpy import ddd as DDD
arcpy.env.cellSize = 30 # DEMs natively at 1m resolution
arcpy.env.overwriteOutput = True
print("Model running, starting timer")
a = time.perf_counter()/60
env = arcpy.env
script = os.path.dirname(sys.argv[0]) # Script location
print("Script containing folder: " + script)
temp = r"memory"
env.workspace = temp

#Load layers
gis = GIS("https://sfsu.maps.arcgis.com/sharing")
dsm = gis.content.get("b690f8d64d0145f1baf74d73690da154")
dem = gis.content.get("1adaa794cbf2477da2660f190c785fa7")
veg = gis.content.get("6341228ec82a4bfbaf52d977a14e99ce")
b = time.perf_counter()/60
print(f"Layers loaded: {round(b - a, 2)} minutes")

#Load vegitation layer
veg2 = veg.layers[0]
veg3 =veg2.url
veg4 = r"memory\veg"
DM.MakeFeatureLayer(veg3, veg4)
c = time.perf_counter()/60
print(f"Veg feature generated: {round(c - b, 2)} minutes")

#Select vegitation type 
selection = 'Forest & Woodland' #input habitat type here
where = "LIFEFORM = '" + selection + "'"
DM.SelectLayerByAttribute(veg4, "NEW_SELECTION", where, None)
d = time.perf_counter()/60
print(f"Veg type selected: {round(d - c, 2)} minutes")

#Make conditional vegitation layer raster
vegCon = r"memory\veg2"
path = script + r"\veg.shp"
CO.FeatureClassToShapefile(veg4, script)
CO.FeatureToRaster(path, "LIFEFORM", vegCon, 30)
e = time.perf_counter()/60
print(f"Veg conditional raster created: {round(e - d, 2)} minutes")

#Load non-normalized digital surface model
dsm2 = dsm.layers[0]
dsm3 = dsm2.url
dsm4 = r"memory\dsm"
dsm5 = r"memory\dsm2"
DM.MakeImageServerLayer(dsm3, dsm4)
DM.Resample(dsm4, dsm5, 30)
f = time.perf_counter()/60
print(f"DSM resampled: {round(f - e, 2)} minutes")

#Load digital elevation model
dem2 = dem.layers[0]
dem3 = dem2.url
dem4 = r"memory\dem"
dem5 = r"memory\dem2"
DM.MakeImageServerLayer(dem3, dem4)
DM.Resample(dem4, dem5, 30)
g = time.perf_counter()/60
print(f"DEM resampled: {round(g - f, 2)} minutes")

#Normalize surface model
ndsm = Minus(dsm5, dem5)
h = time.perf_counter()/60
print(f"nDSM generated: {round(h - g, 2)} minutes")

#Conditional values
demValues = [1000, 2700] #input DEM range of values here
dsmValues = [15, 25] #input DSM range of values here

#Make conditional DEM & DSM layer raster
demCon = Con(dem4, 1, 0, f"VALUE > {demValues[0]} And VALUE < {demValues[1]}")
i = time.perf_counter()/60
print(f"DEM conditional raster created: {round(i - h, 2)} minutes")
dsmCon = Con(ndsm, 1, 0, f"VALUE > {dsmValues[0]} And VALUE < {dsmValues[1]}")
j = time.perf_counter()/60
print(f"DSM conditional raster created: {round(j - i, 2)} minutes")

# Layer Weights, doesn't really effect the model if using 
# boolean rasters like we are now, this model however could use
# continous rasters, in which case these weights would effect model outcomes
vegInput = 2
demInput = 1
dsmInput = 1
inList = [vegInput, demInput, dsmInput]
vegProp = vegInput / sum(inList)
demProp = demInput / sum(inList)
dsmProp = dsmInput / sum(inList)

#Make a table of values
myWSTable = WSTable([[vegCon, "VALUE", vegProp], [demCon, "VALUE", demProp], 
                     [dsmCon, "VALUE", dsmProp]])

# Execute WeightedOverlay
outWeighted = WeightedSum(myWSTable)
k = time.perf_counter()/60   
print(f"Weighted sum complete: {round(k - j, 2)} minutes")
# Save the output
output = script + r"/modeloutput"
outWeighted.save(output)

#Make contour around high habitat probability model regions with highest kernal density
points = script + r"\points.shp"
points2 = script + r"\points2.shp"
CO.RasterToPoint(output, points, "Value")
AN.Select(points, points2, "grid_code > 0.9")
kernal = KernelDensity(points2, "NONE", 100, None, "SQUARE_KILOMETERS", "DENSITIES", "PLANAR")
contour = script + r"\kernal.shp"
DDD.Contour(kernal, contour, 1000, 20, 1, "CONTOUR", None)
l = time.perf_counter()/60   
print(f"Contour complete: {round(l - k, 2)} minutes")

# Clean things up a bit
if arcpy.Exists(path):
    DM.Delete(path)
if arcpy.Exists(points):
    DM.Delete(points)
if arcpy.Exists(points2):
    DM.Delete(points2)
    
#All done
print(f"Model complete, total time elapsed: {round(l - a, 2)} minutes")
print("Files located at: " + script)



