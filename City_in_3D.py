#
# City in 3D : a Rhinoceros script that create buildings according to geojson file and with real elevation by Guillaume Meunier
# 
# -----------------------------------
# Need pygeoj.py & utm.py
# It must be in your script's folder
# -----------------------------------
# TODO :
# 
# -----------------------------------
# 
# Copyright (c) 2016, Guillaume Meunier <alliages@gmail.com> 
# City in 3D is free software; you can redistribute it and/or modify 
# it under the terms of the GNU General Public License as published 
# by the Free Software Foundation; either version 3 of the License, 
# or (at your option) any later version. 
# 
# City in 3D is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of 
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the 
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with City in 3D; If not, see <http://www.gnu.org/licenses/>.
# 
# @license GPL-3.0+ <http://spdx.org/licenses/GPL-3.0+>


"""
#######
version 1.1 bugfix in approximation 2016/06/16
version 1.0 initial release 2016/06/12
-
    Args:
        Geojson file
        elevation file in Bil format
        radius around the address
        address you around which you want to create city
    Returns:
        out: various information
        coordinates: coordinates in JSON format
        properties: properties in JSON format
"""
from System import Object
import collections

import pygeoj #pygeoj.py must be in your script's folder
import utm #pygeoj.py must be in your script's folder -- needed by latlong_to_coord

import Rhino as rh
import Rhino.Geometry as rg
import rhinoscriptsyntax as rs
import scriptcontext as sc
import os
import struct
import math

#####ELEV
import  httplib
import json
import urllib

###############################
###########  VARIOUS  #########
###############################

def nominatim(address):
    """
    transfrom address in lat long coordinates
    """
    url = "http://nominatim.openstreetmap.org/search"
    address = address.replace(" ","+")
    format="jsonv2"
    addressdetails="0"
    polygon_="0"
    limit="1"
    url_totale = url+"?q="+address+"&format="+format+"&addressdetails="+addressdetails+"&polygon_="+polygon_+"&limit="+limit
    request = urllib.urlopen(url_totale)
    try:
        results = json.load(request)
        if 0 < len(results):
            r = results[0]
            return float(r['lat']),float(r['lon'])
        else:
            print 'HTTP GET Request failed.'
    except ValueError, e:
        print 'JSON decode failed: '+str(request)

#EXAMPLE
#a = nominatim("133 rue saint antoine Paris")
#print a['display_name']
#print a['lat']
#print a['lon']        
        
def parseTree(input,i=0):
    """
    get tree depth
    """
    if isinstance (input, list):
        i = parseTree(input[0],i+1)
        return(i)
    else:
        return(i)

def latlong_to_coord(lat,lon):
    """
    need UTM
    #convert lat long to rhino coordinates
    #road zero point in France (middle of Paris)
    """
    
    #used as ZERO in rhino
    ptzero_france_east = 452228.9940197494
    ptzero_france_north = 5411363.8212742545
    
    if not -80.0 <= lat <= 84.0:
        print "Lat not in -80 and +84"
    if not -180.0 <= lon <= 180.0:
        print "long not in -180 and 180"
    loc = utm.from_latlon(lat,lon)
    resX = loc[0]-ptzero_france_east
    resY = loc[1]-ptzero_france_north
    return (resX,resY)


def centroid(points):
    """
    find centroid of points
    """
    x_coords = [p[0] for p in points]
    y_coords = [p[1] for p in points]
    _len = len(points)
    centroid_x = sum(x_coords)/_len
    centroid_y = sum(y_coords)/_len
    return [centroid_x, centroid_y]

def toPt(c,z):
    coord = latlong_to_coord(c[1],c[0])
    return rg.Point3d(coord[0],coord[1],z)

def distance(lat11, lon11, lat22, lon22):
    """
    Calculate the great circle distance between two points 
    on the earth (specified in decimal degrees)
    """
    # convert decimal degrees to radians 
    EARTH_RADIUS = 6371009 #en metre
    #lon1, lat1, lon2, lat2 = map(math.radians, [lon11, lat11, lon22, lat22])
    #lat1 = math.radians(lat11)
    lat1, lng1 = math.radians(lat11), math.radians(lon11)
    lat2, lng2 = math.radians(lat22), math.radians(lon22)
    sin_lat1, cos_lat1 = math.sin(lat1), math.cos(lat1)
    sin_lat2, cos_lat2 = math.sin(lat2), math.cos(lat2)
    delta_lng = lng2 - lng1
    cos_delta_lng, sin_delta_lng = math.cos(delta_lng), math.sin(delta_lng)
    d = math.atan2(math.sqrt((cos_lat2 * sin_delta_lng) ** 2 + (cos_lat1 * sin_lat2 - sin_lat1 * cos_lat2 * cos_delta_lng) ** 2),sin_lat1 * sin_lat2 + cos_lat1 * cos_lat2 * cos_delta_lng)
    return EARTH_RADIUS * d

###############################
########### BIL PARSER ########
###############################

"""
Thanks dbr/Ben
#based upon https://gist.github.com/dbr/3351090
which is mostly based of:
http://stevendkay.wordpress.com/2010/05/29/parsing-usgs-bil-digital-elevation-models-in-python/
Documentation for the format itself:
http://webhelp.esri.com/arcgisdesktop/9.2/index.cfm?TopicName=BIL,_BIP,_and_BSQ_raster_files


#------ BIL EXAMPLE ---------
#bp = BilParser("elevationBil/elev-decoupe75.hdr") # expects to also find filename.bil
#h = bp.header
#v = bp.values
"""

def parse_header(hdr):
    """
    Parse a BIL header .hdr file
    """
    contents = open(hdr).read()
    lines = contents.strip().splitlines()
    header = {}
    for li in lines:
        key, _, value = li.partition(" ")
        header[key] = value.strip()

    return header


def parse_bil(path, rows, cols, dtype):
    # where you put the extracted BIL file
    fi = open(path, "rb")
    contents = fi.read()
    fi.close()

    # unpack binary data into a flat tuple z
    n = int(rows*cols)
    if dtype == "FLOAT":
        s = "<%df" % (n,)
    else: # spec says to assume unsigned int if no type specified..
        s = "<%dH" % (n,) # unsigned int
    z = struct.unpack(s, contents)
    values = [[None for x in range(cols)] for x in range(rows)]
    for r in range(rows):
        for c in range(cols):
            val = z[(cols*r)+c]
            if (val==65535 or val<0 or val>20000):
                # may not be needed depending on format, and the "magic number"
                # value used for 'void' or missing data
                val=0.0
            values[r][c]=float(val)
    return values

class BilParser(object):
    """
    magicin class
    """
    #based upon https://gist.github.com/dbr/3351090
    def __init__(self, headerpath):
        self.basepath = os.path.splitext(headerpath)[0]
        self.header = parse_header(self.basepath + ".hdr")
        self.values = parse_bil(
            self.basepath + ".bil",
            rows = int(self.header['NROWS']),
            cols = int(self.header['NCOLS']),
            dtype = self.header['PIXELTYPE'])

def get_row_and_column(header, latitude, longitude):
    """
    convert from lat/long to row&column
    """
    sizelat = float(header['NROWS'])
    sizelong = float(header['NCOLS'])
    long_space = float(header['XDIM'])
    lat_space = float(header['YDIM'])
    long_min = float(header['ULXMAP'])-(long_space/2)#middle of the band
    lat_max = float(header['ULYMAP'])+(lat_space/2)#middle of the band
    long_max = long_min + (long_space*sizelong)
    lat_min = lat_max - (lat_space*sizelat)
    if not(lat_min < latitude < lat_max):
        print "min:"+str(lat_min)+", max:"+str(lat_max)
        return "latitude outside range | min:"+str(lat_min)+", max:"+str(lat_max)
    if not(long_min < longitude < long_max):
        print "min:"+str(long_min)+", max:"+str(long_max)
        return "longitude outside range | min:"+str(long_min)+", max:"+str(long_max)
    row = int(math.floor((lat_max - latitude) / lat_space))
    column = int(math.floor((longitude - long_min) / long_space))
    #print "R="+str(row)+" | C="+str(column)
    return row,column

def get_lat_and_long(header,row,column):
    """
    convert from row&column to lat/long
    """
    #sizelat = float(header['NROWS'])
    #sizelong = float(header['NCOLS'])
    long_space = float(header['XDIM'])
    lat_space = float(header['YDIM'])
    long_min = float(header['ULXMAP'])#middle of the band
    lat_max = float(header['ULYMAP'])#middle of the band
    #FAIRE DES IFS
    lat = lat_max - (lat_space*row)
    long = long_min + (long_space*column)
    return lat,long

###############################
########### ELEVATION #########
###############################

def bil_elevation(h,v,lat,lon):
    #from bil file, get value
    try:
        row, column = get_row_and_column(h,lat, lon)
    except:
        err = get_row_and_column(h,lat, lon)
        raise Exception(err)
    return v[row][column]

#EXAMPLE    
#el = bil_elevation(h,v,48.7810,2.12594)

def approx_elevation(h,v,lat,lon):
    """
    linear approximation of elevation using bil file
    """
    try:
        row, column = get_row_and_column(h,lat, lon)
    except:
        err = "problem getting row and column"
        raise Exception(err)
    el_c = v[row][column]
    lat_t,long_t = get_lat_and_long(h,row,column)
	dis_c = distance(lat,lon,lat_t,long_t)
    if dis_c == 0:
	    return el_c #case perfectly at center
    dis_c = 1/dis_c
    ##
    el_n = v[row-1][column]
    lat_t,long_t = get_lat_and_long(h,row-1,column)
    dis_n = 1/distance(lat,lon,lat_t,long_t)
    ##
    el_s = v[row+1][column]
    lat_t,long_t = get_lat_and_long(h,row+1,column)
    dis_s = 1/distance(lat,lon,lat_t,long_t)
    ##
    el_e = v[row][column+1]
    lat_t,long_t = get_lat_and_long(h,row,column+1)
    dis_e = 1/distance(lat,lon,lat_t,long_t)
    ##
    el_o = v[row][column-1]
    lat_t,long_t = get_lat_and_long(h,row,column-1)
    dis_o = 1/distance(lat,lon,lat_t,long_t)
    ##
    el_ne = v[row-1][column+1]
    lat_t,long_t = get_lat_and_long(h,row-1,column+1)
    dis_ne = 1/distance(lat,lon,lat_t,long_t)
    ##
    el_se = v[row+1][column+1]
    lat_t,long_t = get_lat_and_long(h,row+1,column+1)
    dis_se = 1/distance(lat,lon,lat_t,long_t)
    ##
    el_so = v[row+1][column-1]
    lat_t,long_t = get_lat_and_long(h,row+1,column-1)
    dis_so = 1/distance(lat,lon,lat_t,long_t)
    ##
    el_no = v[row-1][column-1]
    lat_t,long_t = get_lat_and_long(h,row-1,column-1)
    dis_no = 1/distance(lat,lon,lat_t,long_t)
    ##
    r = (el_c*dis_c+el_n*dis_n+el_s*dis_s+el_e*dis_e+el_o*dis_o+el_no*dis_no+el_ne*dis_ne+el_so*dis_so+el_se*dis_se)/(dis_c+dis_n+dis_s+dis_e+dis_o+dis_no+dis_ne+dis_so+dis_se)
    return r

def google_elevation(lat, lng):
    """
    Get elevation from google elevation API
    it has limitation in time and number of request
    """
    apikey = "USE YOUR OWN KEY"
    url = "https://maps.googleapis.com/maps/api/elevation/json"
    request = urllib.urlopen(url+"?locations="+str(lat)+","+str(lng)+"&key="+apikey)
    try:
        results = json.load(request).get('results')
        if 0 < len(results):
            elevation = results[0].get('elevation')
            return elevation
        else:
            print 'HTTP GET Request failed.'
    except ValueError, e:
        print 'JSON decode failed: '+str(request)

#ELEV EXAMPLE
#print google_elevation(48.8445548,2.4222176)

##############################
##########  EXTRUDE  #########
##############################

def extrude(json, header, v, rayon=None, lat=None, long=None ):
    #main definition
    for feature in json: 
        try:
            coord = feature.geometry.coordinates
        except:
            continue
        prop = feature.properties
        z=0
        if parseTree(coord) == 4:
            coord[0] = coord[0][0]
        c_x, c_y = centroid(coord[0])
        if rayon:
            di = distance(lat,long,c_y,c_x)
            if di>rayon:
                continue
        z = approx_elevation(header,v,c_y,c_x)
        for i in range(len(coord)):
            for j in range(len(coord[i])):
                coord[i][j] = toPt(coord[i][j],z)
            coord[i] = rg.PolylineCurve(coord[i])
        brep_face_GUID = rs.AddPlanarSrf(coord) #GUID
        if "H_MED" in prop:
            h = prop["H_MED"]
        else:
            if "H_MOY" in prop:
                h = prop["H_MOY"]
            else:
                if "H_MAX" in prop:
                    h = prop["H_MAX"]
                else:
                    if "l_plan_h" in prop:
                        h = prop["l_plan_h"]
                        if h is None:
                            h=3
                        else:
                            if h=="R":
                                h=3
                            else:
                                h=float(h[-1])*3
                    else:
                        h = 3
        try:
            extrude_path = rs.AddLine((0,0,0), (0,0,h))
        except:
            print "error extrude"
            continue
        objectref_path = rh.DocObjects.ObjRef(extrude_path)
        path_curve = rh.DocObjects.ObjRef.Curve(objectref_path)
        object_reference = rh.DocObjects.ObjRef(brep_face_GUID[0])
        brep_face = rh.DocObjects.ObjRef.Face(object_reference)
        brep_extrude = rh.Geometry.BrepFace.CreateExtrusion(brep_face, path_curve, True)
        added_brep = sc.doc.Objects.AddBrep(brep_extrude)
        try:
            rs.ObjectName(added_brep,str(prop["OBJECTID"]))
        except:
            rs.ObjectName(added_brep,"noID")
        try:
            rs.DeleteObject(brep_face_GUID)
        except:
            print "error"
        rs.DeleteObject(extrude_path)

###############################
##########   START    #########
###############################

rs.EnableRedraw(False)

#YOUR BASE FOR EXTRUSION FILE AS GEOJSON
#either without path if in same directory or with path
cadastre_f = 'D:/DATA/g.meunier/Desktop/elev/emprise_bati_paris.geojson'

#YOUR ELEVATION FILE AS HDR
# expects to also find bil file in same folder
elevation_f = "elev-decoupe75.hdr"

#IF YOU WANT A SMALL PART OF PARIS (IF YOU DON'T USE ZERO IN  radius_around
#THE ADDRESS YOU WANT
address_f = ""
address_f = "20 rue Gasnier-Guy Paris"

#AND THE RADIUS AROUND THIS ADDRESS IN METER (OR ZERO)
radius_around = 400

#CALCULATION
extrude_json = pygeoj.load(cadastre_f)
elevation_file = BilParser(elevation_f)
h = elevation_file.header
v = elevation_file.values

#test if radius_around>0 or exist
if radius_around:
    if address_f:
        address_coord_lat,address_coord_lon = nominatim(address_f)
        extrude(extrude_json, h, v, radius_around, address_coord_lat, address_coord_lon)
    else:
        print "need an address or no radius"
else:
    extrude(extrude_json, h, v)

#COULD USE MULTITHREADING :
#https://stevebaer.wordpress.com/2011/06/01/multithreaded-python/

print "done"
rs.EnableRedraw(True);