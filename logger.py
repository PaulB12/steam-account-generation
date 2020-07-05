#Paul Brennan - Log
import time
from datetime import datetime

class logger:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

    def fetch_time(self, type):
        if(type):
            return(datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        else:
           return(datetime.now().strftime('%Y-%m-%d')) 

    def log_message(self, message, status):
        if(status == 0):
            #Successful
            print(self.OKGREEN + self.fetch_time(True) + " - " + message + self.ENDC)
        else:
            #Unsuccessful
            print(self.FAIL + self.fetch_time(True) + " - " + message + self.ENDC)
        with open("./logs/"+self.fetch_time(False)+".txt", "a") as log_file:
            textToWrite = message+"\n"
            log_file.writelines(textToWrite)