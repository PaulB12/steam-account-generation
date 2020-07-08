from httpManager import httpManager
from logger import logger
from bs4 import BeautifulSoup
import time

class disposableEmail:

    def __init__(self, username, domain, requestManager):
        self.username = username
        self.domain = domain
        self.email = username + "@" + domain
        self.requestManager = requestManager
        self.log = logger()

    def searchInbox(self, subject,  text_to_find):
        headers = {
            'User-Agent' : 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:77.0) Gecko/20100101 Firefox/77.0',
            'Content-Type': 'application/x-www-form-urlencoded',
            'X-Prototype-Version': '1.7',
            'X-Requested-With': 'XMLHttpRequest',              
            'Accept-Language': 'en-GB',
            'Referer': 'http://store.steampowered.com/join/',
        }
        attempts = 0
        link = False
        skip = False
        while attempts < 5:
            emailResponse = self.requestManager.getRequest('http://generator.email/'+self.email, headers)
            if(emailResponse != False):
                if text_to_find in emailResponse.text:
                    self.log.log_message("Email successfully found, returning the text with search filter => ("+text_to_find+")", 0)
                    skip = True
                    return(emailResponse)
                else:
                    #time.sleep(5)
                    #attempts = attempts + 1
                    soup = BeautifulSoup(emailResponse.text, 'html.parser')
                    try:
                        subjectDivs = soup.find_all('div', {'class':'e7m subj_div_45g45gg'})[0]
                        if subject in subjectDivs.text:
                            link = 'http://generator.email'+(subjectDivs.parent['href'])
                            self.log.log_message("Successfully found an email with the subject => ("+subject+")",0)
                            break
                        else:
                            attempts = attempts + 1
                            time.sleep(5)
                    except Exception as e:
                        attempts = attempts + 1
                        time.sleep(5)
                        pass
                    attempts = attempts + 1
                    time.sleep(5)
            else:
                attempts = attempts + 1
                time.sleep(5)

        if(skip == False and link != False):
            attempts = 0
            while attempts < 3:
                bodyResponse = self.requestManager.getRequest(link, headers)
                if(bodyResponse != False):
                    self.log.log_message("Email successfully found, returning the body text of subject => ("+subject+")", 0)
                    return(bodyResponse)
                else:
                    attempts = attempts + 1
                    time.sleep(5)
            self.log.log_message("Found an email however could not fetch the email with subject => ("+subject+")", 1)
            return(False)
        #else:
        self.log.log_message("Could not find an email in the set amount of time with text => ("+text_to_find+")", 1)
        #    return(False)
        return(False)
