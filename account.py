from httpManager import httpManager
from logger import logger
from captcha import captcha
import time
import Crypto
from Crypto.PublicKey import RSA
from Crypto import Random
from Crypto.PublicKey.RSA import construct
from Crypto.Cipher import PKCS1_v1_5
import base64

class account:
    def __init__(self, proxy, username=None, password=None):
        self.username = username
        self.password = password
        self.log = logger()
        self.requestManager = httpManager()
        self.proxy = proxy

        if self.requestManager.verifyProxy(proxy):
            self.captcha = captcha("2eae7d79735c8ffc13e28dd71bec656f", self.proxy)
            self.status = True
        else:
            #Change this before I go back to production
            self.status = True
    
    def currentMilisecond(self):
        #Used in encrypting password
        return int(round(time.time() * 1000))

    def generateSteamSession(self):
        #We just have to visit the steam home-page in order to get a sessionId & browserId
        if(self.status):
            headers = {
                'User-Agent' : "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:77.0) Gecko/20100101 Firefox/77.0",
                'Content-Type': 'application/x-www-form-urlencoded',              
                'Accept-Language': 'en-GB',
                'Referer': 'http://store.steampowered.com/join/',
            }
            self.requestManager.getRequest("https://store.steampowered.com/", headers, self.proxy)
            return(True)
        else:
            self.log.log_message("A valid proxy must be used in communicating with steam servers", 1)
            return(False)

    def encryptPassword(self):
        if(self.status):
            if(self.username is not None or self.password is not None):
                #Creating neccesary paramters to send the request
                headers = {
                    'User-Agent' : 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:77.0) Gecko/20100101 Firefox/77.0',
                    'Content-Type': 'application/x-www-form-urlencoded',
                    'X-Prototype-Version': '1.7',
                    'X-Requested-With': 'XMLHttpRequest',              
                    'Accept-Language': 'en-GB',
                    'Referer': 'http://store.steampowered.com/join/',
                }
                params = {
                    'donotcache': self.currentMilisecond(),
                    'username': self.username,
                }
                response = self.requestManager.postRequest("https://steamcommunity.com/login/getrsakey/", params, headers, self.proxy)
                if(response != False):
                    json_response = response.json()
                    if(json_response['success']):
                        exp = int(json_response['publickey_exp'], 16)
                        mod = int(json_response['publickey_mod'], 16)

                        pubkey = construct((mod, exp))
                        cipher = PKCS1_v1_5.new(pubkey)
                        message = base64.b64encode(cipher.encrypt((self.password).encode('utf-8'))).decode('utf-8')
                        self.encryptedPassword = message
                        self.encryptedTimestamp = json_response['timestamp']
                        return(True)
                    else:
                        self.log.log_message("A unknown error occured fetching user rsa key, request went through but wrong data returned",1)
                        return(False)
                else:
                    #Log is already handled in httpManager
                    return(False)
            else:
                self.log.log_message("You cannot try to log into an account without a valid username or password", 1)
                return(False)
        else:
            self.log.log_message("A valid proxy must be used in communicating with steam servers", 1)
            return(False)

    def login(self, captcha):
        if(self.generateSteamSession()):
            if captcha:
                captchaAnswer = self.captcha.generateCaptcha()
                captchaGid = captcha.gid
                if(captchaAnswer == False):
                    return(False)
            else:
                captchaGid = -1
                captchaAnswer = ""
            
            if(self.encryptPassword()):
                headers = {
                    'User-Agent' : 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:77.0) Gecko/20100101 Firefox/77.0',
                    'Content-Type': 'application/x-www-form-urlencoded',              
                    'Accept-Language': 'en-GB',
                    'Referer': 'http://store.steampowered.com/join/',
                }
                params = {
                    'captcha_text': captchaAnswer,
                    'captchagid': captchaGid,
                    'donotcache': self.currentMilisecond(),
                    'emailauth': '',
                    'emailsteamid': '',
                    'loginfriendlyname': '',
                    'password': self.encryptedPassword,
                    'remember_login': True,
                    'rsatimestamp': self.encryptedTimestamp,
                    'username': self.username
                }
                loginResponse = self.requestManager.postRequest("https://steamcommunity.com/login/dologin", params, headers, self.proxy)
                if(loginResponse != False):
                    loginResponse = loginResponse.json()
                    if(loginResponse['success']):
                        found = False
                        for cookie in self.requestManager.s.cookies.get_dict():
                            if "steamLoginSecure" in cookie:
                                found = True
                        if(found):
                            headers = {
                                "User-Agent" : "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:77.0) Gecko/20100101 Firefox/77.0",
                                'Content-Type': 'application/x-www-form-urlencoded',              
                                'Accept-Language': 'en-GB',
                                'Referer': 'https://steamcommunity.com/login/home/?goto=',
                            }
                            params = {
                                'steamid': loginResponse['transfer_parameters']['steamid'],
                                'token_secure': loginResponse['transfer_parameters']['token_secure'],
                                'auth': loginResponse['transfer_parameters']['auth'],
                                'remember_login': False
                            }
                            self.requestManager.postRequest('https://store.steampowered.com/login/transfer', params, headers, self.proxy)
                            self.requestManager.postRequest('https://store.steampowered.com/login/transfer', params, headers, self.proxy)
                            self.log.log_message("Logged into steam successfully", 0)
                            return(True)
                    else:
                        self.log.log_message("Failed to log into steam, request was sent but response was a failure", 1)
                        return(False)
                else:
                    return(False)
            else:
                return(False)
            
        else:
            return(False)
        
account = account("", "csgoCommendSgYeTCsO", "O42j4gHbFfG8Kb3u")
print(account.login(False))

