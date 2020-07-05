#Paul Brennan - Requests Manager - Class for dealing with Requests
import requests
import time
import json
from logger import logger
from datetime import datetime

class httpManager:
    def __init__(self, debug=False):
        self.s = requests.Session()
        self.log = logger()
        self.debug = debug
        self.log.log_message("Initalised a new request session",0)
    
    def debugCheck(self, url, headers=None, proxy=None, response=None, params=None):
        if self.debug:
            print("URL => ",url)
            print("Data => ",params)
            print("Headers => ",headers)
            print("Proxy => ",proxy)
            print("Response Code =>",response.status_code)
            for cookie in self.s.cookies:
                print("Cookie",cookie)

    def getRequest(self, url, headers=None, proxy=None):
        #Default config
        if headers is None:
            headers = {
                'Content-Type': 'application/x-www-form-urlencoded',
                'Accept-Language': 'en-GB',
                'Origin': 'https://store.steampowered.com',
                'Referer': 'https://store.steampowered.com',
                'User-Agent' : 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:77.0) Gecko/20100101 Firefox/77.0',
            }
        try:
            response = self.s.get(url, headers=headers, proxies=proxy)
            self.debugCheck(url, headers, proxy, response)
            if(response.status_code == 200):
                self.log.log_message("GET Request to URL ("+url+") responded with status code 200",0)
                return(response)
            else:
                self.log.log_message("GET Request to URL ("+url+") responded with status code ("+str(response.status_code)+")",1)
                return(False)
        except Exception as e:
            self.log.log_message("GET Request to URL ("+url+") responded with a unknown error",1)
            if self.debug:
                print(e)
            return(False)

    def postRequest(self, url, params=None, headers=None, proxy=None):
        #Default config
        if headers is None:
            headers = {
                'Content-Type': 'application/x-www-form-urlencoded',
                'Accept-Language': 'en-GB',
                'Origin': 'https://store.steampowered.com',
                'Referer': 'https://store.steampowered.com',
                'User-Agent' : 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:77.0) Gecko/20100101 Firefox/77.0',
            }
        try:
            response = self.s.post(url, params, headers=headers, proxies=proxy)
            self.debugCheck(url, headers, proxy, response, params)
            if(response.status_code == 200):
                self.log.log_message("POST Request to URL ("+url+") with paramaters ("+json.dumps(params)+") responded with status code 200",0)
                return(response)
            else:
                self.log.log_message("POST Request to URL ("+url+") with paramaters ("+json.dumps(params)+") responded with status code ("+str(response.status_code)+")",1)
                return(False)
        except Exception as e:
            self.log.log_message("POST Request to URL ("+url+") with paramaters ("+json.dumps(params)+") responded with a unknown error",1)
            if self.debug:
                print(e)
            return(False)

    def verifyProxy(self, proxy):
        response = self.getRequest("https://store.steampowered.com/join/ajaxverifyemail")
        if(response != False):
            if "You must verify your" in response.text:
                self.log.log_message("Proxy ("+proxy+") has passed verification",0)
                return(True)
            else:
                self.log.log_message("Proxy ("+proxy+") has failed verification",1)
                return(False)
        else:
            self.log.log_message("Proxy ("+proxy+") has failed verification",1)
            return(False)
