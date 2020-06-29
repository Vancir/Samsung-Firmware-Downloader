# SPDX-License-Identifier: GPL-3.0+
# Copyright (C) 2020 Vancir

# FUS request helper (automatically sign requests and update tokens)

import requests

import auth

class FUSClient(object):
    def __init__(self):
        self.auth = ""
        self.sessid = ""
        self.makereq("NF_DownloadGenerateNonce.do")
    def makereq(self, path, data=""):
        authv = 'FUS nonce="", signature="' + self.auth + '", nc="", type="", realm="", newauth="1"'
        r = requests.post("https://neofussvr.sslcs.cdngc.net/" + path, data=data,
            headers={"Authorization": authv}, cookies={"JSESSIONID": self.sessid})
        if "NONCE" in r.headers:
            self.encnonce = r.headers["NONCE"]
            self.nonce = auth.decryptnonce(self.encnonce)
            self.auth = auth.getauth(self.nonce)
        if "JSESSIONID" in r.cookies:
            self.sessid = r.cookies["JSESSIONID"]
        r.raise_for_status()
        return r.text
    def downloadfile(self, filename):
        authv = 'FUS nonce="' + self.encnonce + '", signature="' + self.auth + '", nc="", type="", realm="", newauth="1"'
        r = requests.get("https://cloud-neofussvr.sslcs.cdngc.net/NF_DownloadBinaryForMass.do",
            params={"file": filename}, headers={"Authorization": authv}, stream=True)
        r.raise_for_status()
        return r
