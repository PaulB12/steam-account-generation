from httpManager import httpManager
from logger import logger
from captcha import captcha
from disposableEmail import disposableEmail
import time
import Crypto
import json
from Crypto.PublicKey import RSA
from Crypto import Random
from Crypto.PublicKey.RSA import construct
from Crypto.Cipher import PKCS1_v1_5
import base64

class account:
    def __init__(self, proxy, path="./accounts/not_defined.txt", username=None, password=None, domain=None):
        self.username = username
        self.password = password
        self.path = path
        self.log = logger()
        self.requestManager = httpManager(True)
        self.proxy = proxy
        self.domain = domain
        if(username is not None and domain is not None):
            self.email = disposableEmail(self.username, self.domain, self.requestManager)
        

        if self.requestManager.verifyProxy(proxy):
            self.captcha = captcha("2eae7d79735c8ffc13e28dd71bec656f", self.proxy, self.requestManager)
            self.status = True
        else:
            #Change this before I go back to production
            self.status = False
    
    def currentMilisecond(self):
        #Used in encrypting password
        return int(round(time.time() * 1000))

    def generateSteamSession(self):
        #We just have to visit the steam home-page in order to get a sessionId & browserId
        if(self.status):
            resp = self.requestManager.getRequest("https://steamcommunity.com/", None, self.proxy)
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
                    'Accept-Language': 'en-GB',
                    'Referer': 'http://store.steampowered.com/join/',
                    'Sec-Fetch-Dest': 'empty',
                    'Sec-Fetch-Mode': 'cors',
                    'Sec-Fetch-Site': 'same-origin',
                    'X-Requested-With': 'XMLHttpRequest',
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

    def login(self, captcha, gid=None):
        if(self.generateSteamSession()):
            self.requestManager.getRequest('https://steamcommunity.com/login/', None, self.proxy)
            if captcha:
                captchaAnswer = self.captcha.generateCaptcha(gid)
                captchaGid = self.captcha.gid
                if(captchaAnswer == False):
                    return(False)
            else:
                captchaGid = -1
                captchaAnswer = ""
            if gid is not None:
                captchaGid = gid
            
            if(self.encryptPassword()):
                headers = {
                    'User-Agent' : 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:77.0) Gecko/20100101 Firefox/77.0',
                    'Content-Type': 'application/x-www-form-urlencoded',
                    'X-Requested-With': 'XMLHttpRequest',              
                    'Accept-Language': 'en-GB',
                    'Referer': 'http://store.steampowered.com/join/',
                    'Sec-Fetch-Dest': 'empty',
                    'Sec-Fetch-Mode': 'cors',
                    'Sec-Fetch-Site': 'same-origin'
                }
                params = {
                    'captcha_text': '',
                    'captchagid': -1,
                    'donotcache': self.currentMilisecond(),
                    'emailauth': '',
                    'emailsteamid': '',
                    'loginfriendlyname': '',
                    'password': self.encryptedPassword,
                    'remember_login': False,
                    'rsatimestamp': self.encryptedTimestamp,
                    'username': self.username,
                    'twofactorcode': '',
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
                        print(loginResponse)
                        self.log.log_message("Failed to log into steam, request was sent but response was a failure", 1)
                        return(False)
                else:
                    return(False)
            else:
                return(False)
            
        else:
            return(False)
    
    def activateSteamGuardEmail(self):
        if(self.status): 
            emailResponse = self.email.searchInbox("Steam Guard", "disableverification")
            if(emailResponse != False):
                try:
                    steamUrl = "https://store.steampowered.com/account/steamguarddisableverification?stoken="+emailResponse.text.split("https://store.steampowered.com/account/steamguarddisableverification?stoken=")[1].split('"')[0].replace("&amp;","&")
                    headers = {
                        'Content-Type': 'application/x-www-form-urlencoded',
                        'Accept-Language': 'en-GB',
                        'Origin': 'https://store.steampowered.com',
                        'Referer': 'https://store.steampowered.com/twofactor/manage_action',
                        'User-Agent' : 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:77.0) Gecko/20100101 Firefox/77.0'
                    }
                    steamGuardDisable = self.requestManager.getRequest(steamUrl, headers, self.proxy)
                    if(steamGuardDisable != False):
                        self.log.log_message("Successfully disabled steam guard for the account", 0)
                        return(True)
                    else:
                        self.log.log_message("Failed to disable steam guard from the given link", 1)
                        return(False)
                except Exception as e:
                    print(e)
                    self.log.log_message("Failed to fetch steam guard link from email response", 1)
                    return(False)
            else:
                self.log.log_message("Failed to find steam guard email", 1)
                return(False)
        else:
            self.log.log_message("A valid proxy must be used in communicating with steam servers", 1)
            return(False)

    def disableSteamGuard(self):
        if(self.status):
            headers = {
                'Content-Type': 'application/x-www-form-urlencoded',
                'Accept-Language': 'en-GB',
                'Origin': 'https://store.steampowered.com',
                'Referer': 'https://store.steampowered.com/twofactor/manage_action',
                'User-Agent' : 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:77.0) Gecko/20100101 Firefox/77.0'
            }
            params = {
                'action': 'actuallynone',
                'sessionid': self.requestManager.s.cookies['sessionid'],
                'none_authenticator_check': 'on'
            }
            steamGuardResponse = self.requestManager.postRequest('https://store.steampowered.com/twofactor/manage_action', params, headers, self.proxy)
            if(steamGuardResponse != False):
                self.log.log_message("Successfully sent the first Steam Guard disable request (manage action)", 0)
                params = {
                    'action': 'actuallynone',
                    'sessionid': self.requestManager.s.cookies['sessionid']
                }
                steamGuardSecondResponse = self.requestManager.postRequest('https://store.steampowered.com/twofactor/manage_action', params, headers, self.proxy)
                if(steamGuardSecondResponse != False):
                    self.log.log_message("Successfully sent the second Steam Guard disable request (manage action)", 0)
                    #Search for the email now
                    if(self.activateSteamGuardEmail()):
                        return(True)
                    else:
                        return(False)
                else:
                    return(False)
                
            else:
                return(False)
        else:
            self.log.log_message("A valid proxy must be used in communicating with steam servers", 1)
            return(False)

    def checkName(self):
        if(self.status):
            self.generateSteamSession()
            headers = {
                'User-Agent' : 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:77.0) Gecko/20100101 Firefox/77.0',
                'Content-Type': 'application/x-www-form-urlencoded',
                'X-Requested-With': 'XMLHttpRequest',
                'Accept-Language': 'en-GB',
            }
            params = {
                 'accountname': self.username,
                 'count': 1,
            }
            nameResponse = self.requestManager.postRequest('https://store.steampowered.com/join/checkavail/', params, headers, self.proxy)
            if(nameResponse != False):
                nameResponse = nameResponse.json()
                if(nameResponse['bAvailable']):
                    self.log.log_message("The username ("+self.username+") is avaliable", 0)
                    return(True)
                else:
                    self.log.log_message("The username ("+self.username+") is taken", 1)
                    return(False)
            else:
                return(False)
        else:
            self.log.log_message("A valid proxy must be used in communicating with steam servers", 1)
            return(False)

    def finishSteamAccountCreation(self, creationId):
        if(self.status):
            headers = {
               'Content-Type': 'application/x-www-form-urlencoded',
                'Accept-Language': 'en-GB',
                'Origin': 'https://store.steampowered.com',
                'Referer': 'https://store.steampowered.com/join/completesignup?&snr=1_60_4__62&creationid='+creationId,
                "User-Agent" : "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:77.0) Gecko/20100101 Firefox/77.0",
                'X-Requested-With': 'XMLHttpRequest',
                'X-Prototype-Version': '1.7',
                'Sec-Fetch-Dest': 'empty',
                'Sec-Fetch-Mode': 'cors',
                'Sec-Fetch-Site': 'same-origin'
            }
            params = {
                'accountname': self.username,
                'password': self.password,
                'count': 4,
                'lt': 0,
                'creation_sessionid': creationId,
            }
            response =  self.requestManager.postRequest("https://store.steampowered.com/join/createaccount/", params, headers, self.proxy)
            if(response != False):
                print(response.text)
                time.sleep(30)
                return(True)
            else:
                return(False)
        else:
            self.log.log_message("A valid proxy must be used in communicating with steam servers", 1)
            return(False)

    def sendSteamAccountCreation(self):
        if(self.status):
            if(self.email is not None):
                headers = {
                    'Content-Type': 'application/x-www-form-urlencoded',
                    'Accept-Language': 'en-GB',
                    'Origin': 'https://store.steampowered.com',
                    'Referer': 'https://store.steampowered.com/join/',
                    'User-Agent' : 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:77.0) Gecko/20100101 Firefox/77.0',
                    'X-Requested-With': 'XMLHttpRequest'
                }
                captchaResponse = self.captcha.generateCaptcha()
                if(captchaResponse != False):
                    params = {
                        'email': self.username + "@" + self.domain,
                        'captchagid': self.captcha.gid,
                        'captcha_text': captchaResponse
                    }
                    steamCaptchaSend = self.requestManager.postRequest('https://store.steampowered.com/join/ajaxverifyemail', params, headers, self.proxy)
                    if(steamCaptchaSend != False):
                        steamCaptchaSend = steamCaptchaSend.json()
                        captchaReport = True
                        status = False
                        if(steamCaptchaSend['success'] == 1):
                            #Continue
                            steamEmailResponse = self.findSteamAccountCreationEmail()
                            if(steamEmailResponse != False):
                                resp = self.requestManager.getRequest(steamEmailResponse, headers, self.proxy)
                                creationId = steamEmailResponse.split("creationid=")[1]
                                if(self.finishSteamAccountCreation(creationId)):
                                    #Account Creation is done.
                                    self.requestManager.s.cookies.clear()
                                    if(self.login(False)):
                                        print("Account created => Quickly enable steam guard")
                                        time.sleep(30)
                                        if(self.disableSteamGuard()):
                                            status = True
                                            with open(self.path, "a") as file:
                                                message = self.username + ":" + self.password + "\n"
                                                file.writelines(message)
                                            self.log.log_message("Successfully created the account ("+self.username+")", 0)
                               #     else:
                               #     #One attempt at logging in with captcha
                               #         self.log.log_message("Failed to login to the account ("+self.username+") => Trying with a captcha", 1)
                               #         if self.login(True):
                               #             if(self.disableSteamGuard()):
                               #                 status = True
                               #                 with open(self.path, "a") as file:
                               #                     message = self.username + ":" + self.password + "\n"
                               #                     file.writelines(message)
                               #                 self.log.log_message("Successfully created the account ("+self.username+")")
                                        #else:
                                         #   self.log.log_message("Failed to login to the account ("+self.username+")", 1)
                        elif(steamCaptchaSend['success'] == 2):
                            #Bad captcha, let's report
                            captchaReport = False
                            self.log.log_message('Failed to create steam account, captcha was incorrectly solved',1)

                        elif(steamCaptchaSend['success'] == 105 or steamCaptchaSend['success'] == 84):
                            self.log.log_message('Steam has blocked proxy ('+self.proxy+') failed to communicate', 1)

                        else:
                            print(steamCaptchaSend)
                            self.log.log_message("Unknown issue communicating with steam servers",1)

                        #Captcha Reporting
                        self.captcha.reportCaptcha(captchaReport)
                        return(status)
                    else:
                        self.log.log_message('Failed to communicate with steam servers', 1)
                        return(False)
                else:
                    return(False)
            else:
                self.log.log_message('You must supply an username & email in order to generate an account',1)
                return(False)
        else:
            self.log.log_message('A valid proxy must be used in communicating with steam servers',1)
            return(False)

    def steamLogout(self):
        if(self.status):
            params = {
                'sessionid':self.requestManager.s.cookies['sessionid']
            }
            self.requestManager.postRequest('https://store.steampowered.com/logout/', params)
            return(True)
        else:
            self.log.log_message("A valid proxy must be used in communicating with steam servers", 1)
            return(False)

    def refreshCaptcha(self):
        if self.status:
            params = {'sessionid': self.requestManager.s.cookies['sessionid']}
            response = self.requestManager.postRequest('https://steamcommunity.com/login/refreshcaptcha/', None, None, self.proxy)
            print(response.text)
        else:
            self.log.log_message("A valid proxy must be used in communicating with steam servers", 1)
            return(False)

    def findSteamAccountCreationEmail(self):
        if(self.status): 
            emailResponse = self.email.searchInbox("Steam Account Email", "newaccountverification")
            if(emailResponse != False):
                try:
                    steamUrl = "https://store.steampowered.com/account/newaccountverification?stoken="+emailResponse.text.split("https://store.steampowered.com/account/newaccountverification?stoken=")[1].split('"')[0].replace("&amp;","&")
                    headers = {
                        'Content-Type': 'application/x-www-form-urlencoded',
                        'Accept-Language': 'en-GB',
                        'Origin': 'https://store.steampowered.com',
                        'Referer': 'https://store.steampowered.com/join/',
                        'User-Agent' : 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:77.0) Gecko/20100101 Firefox/77.0',
                        'X-Requested-With': 'XMLHttpRequest'
                    }
                    print(steamUrl)
                    steamGuardCreation = self.requestManager.getRequest(steamUrl, headers, self.proxy)
                    if(steamGuardCreation != False):
                        self.log.log_message("Successfully found the verification url for account ("+self.username+")", 0)
                        return(steamUrl)
                    else:
                        self.log.log_message("Failed to find account verification link", 1)
                        return(False)
                except Exception as e:
                    self.log.log_message("Failed to fetch steam verification from email response", 1)
                    return(False)
            else:
                print(emailResponse)
                self.log.log_messa
                ge("Failed to find steam verification email", 1)
                return(False)
        else:
            self.log.log_message("A valid proxy must be used in communicating with steam servers", 1)
            return(False)


proxy = {'https': '37.1.202.147:3128'}
account = account(proxy, "./accounts/test_accounts.txt", "teeceesesd7988327s1", "O42j4gbse3u", "duybuy.com")

if(account.login(False)):
    print(account.disableSteamGuard())
else:
    print(account.refreshCaptcha())

for cookie in account.requestManager.s.cookies:
    print(cookie)

