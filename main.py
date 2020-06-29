# SPDX-License-Identifier: GPL-3.0+
# Copyright (C) 2020 Vancir

import os
import xml.etree.ElementTree as ET
from clint.textui import progress

import request
import crypt
import fusclient
import versionfetch

MODELS = 'assets/model.txt'
REGIONS = 'assets/region.txt'
DOWNLOC = 'samsung-firmware'

def getbinaryfile(client, fw, region, model):
    try:
        req = request.binaryinform(fw, region, model, client.nonce)
        resp = client.makereq("NF_DownloadBinaryInform.do", req)
        root = ET.fromstring(resp)
        filename = root.find("./FUSBody/Put/BINARY_NAME/Data").text
        path = root.find("./FUSBody/Put/MODEL_PATH/Data").text
        return path, filename
    except:
        return None, None

def initdownload(client, filename):
    req = request.binaryinit(filename, client.nonce)
    resp = client.makereq("NF_DownloadBinaryInitForMass.do", req)

def checkupdate(model, region):
    fw = versionfetch.getlatestver(region, model)
    return fw

def download(version, model, region, outdir):
    client = fusclient.FUSClient()
    path, filename = getbinaryfile(client, version, region, model)
    if not all([path, filename]): return None

    print("Downloading file {} ...".format(path+filename))
    initdownload(client, filename)
    r = client.downloadfile(path+filename)
    length = int(r.headers["Content-Length"])
    output = os.path.join(outdir, filename)
    with open(output, "wb") as f:
        for chunk in progress.bar(r.iter_content(chunk_size=0x10000), expected_size=(length/0x10000)+1):
            if not chunk: continue
            f.write(chunk)
            f.flush()
    return output

def decrypt4(version, model, region, infile, outfile):
    key = crypt.getv4key(version, model, region)
    print("Decrypting with key {}...".format(key.hex()))
    length = os.stat(infile).st_size
    with open(infile, "rb") as inf:
        with open(outfile, "wb") as outf:
            crypt.decrypt_progress(inf, outf, key, length)

def decrypt2(version, model, region, infile, outfile):
    key = crypt.getv2key(version, model, region)
    print("Decrypting with key {}...".format(key.hex()))
    length = os.stat(infile).st_size
    with open(infile, "rb") as inf:
        with open(outfile, "wb") as outf:
            crypt.decrypt_progress(inf, outf, key, length)

def main():
    with open(MODELS, 'r') as fp:
        models = [line.strip() for line in fp.readlines()]
    
    with open(REGIONS, 'r') as fp:
        regions = [line.strip()[line.rfind('(')+1:-1] for line in fp.readlines()]
        # regions = ('CHM', 'CTC', 'CHC', 'BTU')
        
    for model in models:
        for region in regions:
            version = checkupdate(model, region)
            if not version: continue
            print(model, region, version)

            outdir = os.path.join(DOWNLOC, model, region)
            os.system('mkdir -p {}'.format(outdir))

            localpath = download(version, model, region, outdir)
            if not localpath: 
                os.system("rmdir {}".format(outdir))
                continue

            if localpath.endswith('enc2'):
                decrypt2(version, model, region, localpath, localpath.rstrip('.enc2'))
            elif localpath.endswith('enc4'):
                decrypt4(version, model, region, localpath, localpath.rstrip('.enc4'))                

if __name__ == "__main__":
    main()
