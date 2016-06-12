# City in 3D

a Rhinoceros script that create buildings according to geojson file and with real elevation by Guillaume Meunier
 
<img src="https://alliages.files.wordpress.com/2016/06/city-in-3d_a.jpg" style="width: 400px;"/>
-----------------------------------
How to create a city like Paris in 3D?

First you can get open data from the wonderful Apur (http://www.apur.org) that use the ODbL licence (Open Database License)
http://cassini.apur.opendata.arcgis.com/datasets/0eede2e679394258976b57745ba17fd7_0

then thanks to Qgis (http://www.qgis.org) you can convert the file in GEOJSON (http://geojson.org/)

So now you can extrude and have a 3D file.

Then you want to have the right elevation. Again thanks to opendata you can download USGS elevation dataset (http://earthexplorer.usgs.gov/) (the GMTED2010 data) and convert it in Bil format again with QGis

Finally you can convert an address into coordinates using Nominatim (http://nominatim.openstreetmap.org/)

---
#Need 
- pygeoj.py from Karim Bahgat (2015)
- utm.py from Tobias Bieniek (2012)

It must be in your script's folder

---
#TODO
- real roof
- better elevation
- save datas in objects
- create a 3D database

---

Copyright (c) 2016, Guillaume Meunier <alliages@gmail.com> 
City in 3D is free software; you can redistribute it and/or modify 
it under the terms of the GNU General Public License as published 
by the Free Software Foundation; either version 3 of the License, 
or (at your option) any later version. 

City in 3D is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of 
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the 
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with City in 3D; If not, see <http://www.gnu.org/licenses/>.

@license GPL-3.0+ <http://spdx.org/licenses/GPL-3.0+>

---
version 1.0 initial release
---
    Args:
        Geojson file
        elevation file in Bil format
        radius around the address
        address around which you want to create city
    Returns:
        3D Model with elevation
        Each object with it's name corresponding to database
