#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  drvutils module
#
#  Copyright © 2019 Favourix <vladimir.kokes@favourix.com
#  This file is part of fx-drivers (Favourix OS Driver manager).
#
#  Favourix is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 3 of the License, or
#  (at your option) any later version.
#
#  Favourix is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#
#  You should have received a copy of the GNU General Public License
#  along with Favourix; If not, see <http://www.gnu.org/licenses/>.


import subprocess



"""
Returns string with information about GPU and kernel driver in use
"""
def get_gpu():
    from subprocess import check_output
    gpu = check_output('lspci | grep VGA | cut -d ":" -f3', shell=True)
    return gpu 

"""
Returns string with name of GPU vendor
"""
def get_gpu_vendor():
    gpu=get_gpu()
    gpu=gpu.lower()
    
    if ("nvidia" in str(gpu)):
        vendor="nvidia"
    elif ("amd" or "advanced micro devices" in str(gpu)):
        vendor="amd"
    elif ("ati" in str(gpu)):
        vendor= "ati"
    elif ("intel" in str(gpu)):
        vendor="intel"
    elif ("virtualbox" in str(gpu)):
        vendor="virtualbox"
    else :
        vendor="unknown"

    return vendor

def get_gpu_vendor_id():
    gpu=get_gpu()
    gpu=gpu.lower()
    
    if ("nvidia" in str(gpu)):
        vendor_id="0x10de"
    elif ("amd" or "advanced micro devices" in str(gpu)):
        vendor_id="amd"
    elif ("ati" in str(gpu)):
        vendor_id= "ati"
    elif ("intel" in str(gpu)):
        vendor_id="intel"
    elif ("virtualbox" in str(gpu)):
        vendor_id="virtualbox"
    else :
        vendor_id="unknown"

    return vendor_id    

def get_gpu_name():
    from subprocess import check_output
    gpu_name=str(get_gpu())
    
    gpu_name = gpu_name.replace("b' ", "")
    gpu_name = gpu_name.replace("\\n'", "")
    return gpu_name
         


