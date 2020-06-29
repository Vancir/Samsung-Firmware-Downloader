# SPDX-License-Identifier: GPL-3.0+
# Copyright (C) 2020 Vancir

# Get the latest firmware version for a device.

import xml.etree.ElementTree as ET
import requests

def getlatestver(region, model):
    r = requests.get("http://fota-cloud-dn.ospserver.net/firmware/" + region + "/" + model + "/version.xml")
    if r.status_code != 200: return ''
    
    root = ET.fromstring(r.text)
    vercode = root.find("./firmware/version/latest").text
    if not vercode: return ''

    vc = vercode.split("/")    
    return vercode if len(vc) == 4 else vercode + "/" + vc[0]