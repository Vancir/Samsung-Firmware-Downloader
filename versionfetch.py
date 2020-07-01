# SPDX-License-Identifier: GPL-3.0+
# Copyright (C) 2020 Vancir

# Get the latest firmware version for a device.

import xml.etree.ElementTree as ET
import requests

def getver(vercode):
    vc = vercode.split("/")
    version = vercode if len(vc) == 4 else vercode + "/" + vc[0]
    return version.strip()

def getlatestver(region, model):
    avaivers = []
    
    try:
        r = requests.get("http://fota-cloud-dn.ospserver.net/firmware/{}/{}/version.xml".format(region, model))
        if r.status_code != 200: return avaivers
    except:
        return avaivers

    root = ET.fromstring(r.content)
    vercode = root.find("./firmware/version/latest")
    if vercode.text:
        latestver = getver(vercode.text)
        avaivers.append(latestver)

    upgrades =  root.findall("./firmware/version/upgrade/value")
    for ug in upgrades:
        if not ug.text: continue
        upgradever = getver(ug.text)
        avaivers.append(upgradever)

    return avaivers