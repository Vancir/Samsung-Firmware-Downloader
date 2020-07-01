# SPDX-License-Identifier: GPL-3.0+
# Copyright (C) 2020 Vancir

import os
from time import sleep
from queue import Queue
from threading import Thread
import xml.etree.ElementTree as ET
from clint.textui import progress

import request
import crypt
import fusclient
from versionfetch import getlatestver

THREADNUM = 4
MODELS = 'assets/model.txt'
REGIONS = 'assets/region.txt'
DOWNLOC = 'samsung-firmware'

class ProcessThread(Thread):

    def __init__(self, task_queue, name='ProcessThread'):
        super().__init__()
        self._name = name
        self._task_queue = task_queue

    def run(self):
        while True:
            print("{}: remaining {} tasks.".format(
                self._name, self._task_queue.qsize()
            ))

            process_item = self._task_queue.get()
            try:
                self.pipeline(process_item)
            except Exception as e:
                print(e)
            finally:
                self._task_queue.task_done()
                sleep(1)
    
    def pipeline(self, item):
        model = item['Model']
        region = item['Region']
        version = item['Version']

        outdir = os.path.join(DOWNLOC, model, region, version)
        if os.path.exists(outdir):
            print("Already processed, {}/{}/{}".format(model, region, version))
            return
        else:
            os.makedirs(outdir, exist_ok=True)

        localpath = download(version, model, region, outdir)
        if not localpath: 
            os.rmdir(outdir)
            return

        if localpath.endswith('enc2'):
            decrypt2(version, model, region, localpath)
        elif localpath.endswith('enc4'):
            decrypt4(version, model, region, localpath)

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

def download(version, model, region, outdir):
    client = fusclient.FUSClient()
    path, filename = getbinaryfile(client, version, region, model)
    if not all([path, filename]): return None

    output = os.path.join(outdir, filename)
    if os.path.exists(output): return output

    print("Downloading file {} ...".format(path+filename))
    initdownload(client, filename)
    r = client.downloadfile(path+filename)
    length = int(r.headers["Content-Length"])

    with open(output, "wb") as f:
        for chunk in progress.bar(r.iter_content(chunk_size=0x10000), expected_size=(length/0x10000)+1):
            if not chunk: continue
            f.write(chunk)
            f.flush()
    return output

def decrypt4(version, model, region, infile):
    key = crypt.getv4key(version, model, region)
    print("Decrypting with key {}...".format(key.hex()))
    length = os.stat(infile).st_size
    outfile = infile.rstrip('.enc4')
    with open(infile, "rb") as inf:
        with open(outfile, "wb") as outf:
            crypt.decrypt_progress(inf, outf, key, length)
    return outfile

def decrypt2(version, model, region, infile):
    key = crypt.getv2key(version, model, region)
    print("Decrypting with key {}...".format(key.hex()))
    length = os.stat(infile).st_size
    outfile = infile.rstrip('.enc2')
    with open(infile, "rb") as inf:
        with open(outfile, "wb") as outf:
            crypt.decrypt_progress(inf, outf, key, length)
    return outfile

def main():

    with open(MODELS, 'r') as fp:
        models = [line.strip() for line in fp.readlines()]
    
    with open(REGIONS, 'r') as fp:
        regions = [line.strip()[line.rfind('(')+1:-1] for line in fp.readlines()]
        # regions = ('CHM', 'CTC', 'CHC', 'BTU')
    
    processQueue = Queue()
    for model in models:
        for region in regions:
            versions = getlatestver(region, model)            
            for version in versions:
                processQueue.put({
                    'Model': model,
                    'Region': region,
                    'Version': version
                })
                print(model, region, version)

    print("Total tasks number: {}".format(processQueue.qsize()))

    processThreads = []
    for i in range(THREADNUM):
        procthread = ProcessThread(
            task_queue = processQueue,
            name = "ProcessThread{:02d}".format(i+1)
        )
        processThreads.append(procthread)
        procthread.start()

    processQueue.join()

if __name__ == "__main__":
    main()