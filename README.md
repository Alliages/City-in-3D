# City-in-3D
#
# a Rhinoceros script that create buildings according to geojson file and with real elevation by Guillaume Meunier
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
version 1.0 initial release
-
    Args:
        Geojson file
        elevation file in Bil format
        radius around the address
        address you around which you want to create city
    Returns:
        out: various information
        coordiantes: coordinates in JSON format
        properties: properties in JSON format
"""
