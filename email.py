from httpManager import httpManager
from logger import logger
from bs4 import BeautifulSoup
class email:

    def __init__(self, username, domain, requestManager):
        self.username = username
        self.domain = domain
        self.email = username + "@" + domain
        self.requestManager = requestManager

    def searchInbox(self, subject):
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
        while attempts < 5:
            emailResponse = self.requestManager.getRequest('http://generator.email/'+self.email, headers)
            if(emailResponse != False):
                soup = BeautifulSoup(emailResponse.text, 'html.parser')
                subjectDivs = soup.find_all('div', {'class':'e7m subj_div_45g45gg'})[0]
                if subject in subjectDivs.text:
                    link = 'http://generator.email'+(subjectDivs.parent['href'])
                    self.log.log_message("Successfully found an email with the subject => ("+subject+")",0)
                    break
                else:
                    attempts = attempts + 1
                    time.sleep(5)
                break
            else:
                attempts = attempts + 1
                time.sleep(5)
        if(link != False):
            attempts = 0
            while attempts < 3:
                bodyResponse = self.requestManager.getRequest(link, headers)
                if(bodyResponse != False):
                    self.log.log_message("Email successfully found, returning the body text of subject => ("+subject+")", 1)
                    return(bodyResponse.text)
                else:
                    attempts = attempts + 1
            self.log.log_message("Found an email however could not fetch the email with subject => ("+subject+")", 1)
            return(False)
        else:
            self.log.log_message("Could not find an email in the set amount of time with subject => ("+subject+")", 1)
            return(False)

requestManager = httpManager(True)
email = email("csgocommendfyyyemrpsjb", "jueg.app", requestManager)
email.searchInbox("Steam Guard")
