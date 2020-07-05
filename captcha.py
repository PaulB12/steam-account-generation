from httpManager import httpManager
from logger import logger
from time import sleep
import time
import json

class captcha:

    def __init__(self, captchaKey, proxy):
        self.apiKey = captchaKey
        self.requestManager = httpManager()
        self.log = logger()
        self.proxy = proxy

        if self.requestManager.verifyProxy(proxy):
            self.status = True
        else:
            #Change this before I go back to production
            self.status = True

    def fetchSteamSiteKey(self):
        if(self.status):
            headers = {
                'User-Agent' : 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:77.0) Gecko/20100101 Firefox/77.0',
                'Content-Type': 'application/x-www-form-urlencoded',
                'X-Prototype-Version': '1.7',
                'X-Requested-With': 'XMLHttpRequest',              
                'Accept-Language': 'en-GB',
                'Referer': 'http://store.steampowered.com/join/',
            }
            params = { 'count': 1 }
            response = self.requestManager.postRequest('https://store.steampowered.com/join/refreshcaptcha/', params, headers, self.proxy)
            if(response != False):
                json_response = response.json()
                self.siteKey = json_response['sitekey']
                self.log.log_message("Successfully fetched Steam Captcha Information: siteKey => ("+self.siteKey+") gid => ("+json_response['gid']+")", 0)
                self.gid = json_response['gid']
                return(json_response['gid'])
            else:
                return(False)
        else:
            self.log.log_message("You can not generate a steam captcha without having a valid proxy",1)
            return(False)

    def checkCaptcha(self):
        if(self.captchaId is not None):
            url = "http://2captcha.com/res.php?key={}&action=get&id={}&json=1".format(self.apiKey, self.captchaId)
            captchaResponse = self.requestManager.getRequest(url)
            if(captchaResponse != False):
                captchaJson = captchaResponse.json()
                if(captchaJson['status']):
                    captchaAnswer = captchaJson['request']
                    self.log.log_message("CaptchaID => ("+self.captchaId+") answer returned successfully ", 0)
                    return(captchaAnswer)
                else:
                    if(captchaJson['request'] == 'CAPCHA_NOT_READY'):
                        time.sleep(5)
                        self.checkCaptcha()
                    else:
                        self.log.log_message("A captcha error has occured => Dump ("+json.dumps(captchaJson)+")", 1)
                        return(False)
            else:
                return(False)
        else:
            self.log.log_message("Can not check a captchaId that does not exist", 1)
            return(False)

    def generateCaptcha(self):
        captchaResponse = self.sendCaptchaRequest()
        if(captchaResponse != False):
            self.checkCaptcha()
        else:
            self.log.log_message("Captcha request has failed", 1)

    def sendCaptchaRequest(self):
        steamCaptchaGid = self.fetchSteamSiteKey()
        if(steamCaptchaGid != False):
            self.log.log_message("Generating captcha", 0)
            url = 'https://store.steampowered.com/join'
            url = "http://2captcha.com/in.php?key={}&method=userrecaptcha&googlekey={}&pageurl={}&json=1".format(self.apiKey, self.siteKey, url)
            captchaResponse = self.requestManager.postRequest(url)
            if(captchaResponse != False):
                jsonResponse = captchaResponse.json()
                if(jsonResponse['status']):
                    self.captchaId = jsonResponse['request']
                    self.log.log_message("Successfuly sent a captcha request: CaptchaId => ("+self.captchaId+")",0)
                    return(self.captchaId)
                else:
                    self.log.log_message(json.dumps(jsonResponse), 1)
                    return(False)
            else:
                return(False)
        else:
            return(False)

    def reportCaptcha(self, good):
        if(self.captchaId is not None):
            if(good):
                url = "http://2captcha.com/res.php?key={}&action=reportbad&id={}".format(self.apiKey, self.siteKey, self.captchaId)
                msg = "good"
            else:
                url = "http://2captcha.com/res.php?key={}&action=reportgood&id={}".format(self.apiKey, self.siteKey, self.captchaId)
                msg = "bad"
            response = self.requestManager.getRequest(url)
            if(response != False):
                self.log.log_message("Capthca ID ("+self.captchaId+") was successfully reported as "+msg, 0)
                return(True)
            else:
                #Request manager handles this error
                return(False)
        else:
            self.log.log_message("Cannot report a captcha that doesn't exist",1)

#captcha = captcha("2eae7d79735c8ffc13e28dd71bec656f", "")
#captcha.generateCaptcha()