import urllib.request
import datetime as dt
import json
import re
from bs4 import BeautifulSoup
import pytz

class Parser():
    def __init__(self, executer):
        self.executer = executer
        self.lastUpdatedDay = None
        self.updateAtHour = 9
        self.hladina = 0
        self.sunset = 0
        self.sunrise = 0

    def parsePovodia(self):
        if (self.lastUpdatedDay != dt.datetime.now().day) or (self.lastUpdatedDay == None):
            self.lastUpdatedDay = dt.datetime.now().day
            url = 'http://www.povodia.sk/bh/sk/mereni_28.htm'
            with urllib.request.urlopen(url) as response:
               page = response.read()
            soup = BeautifulSoup(page, 'html.parser')
            soup.prettify()
            #print(len(soup.find_all('table')[5]))
            self.hladina = soup.find_all('table')[8].find_all('font', class_='text1bold')[1].string.strip()
            return self

    def getTimeFromFormat(self, timeString):
        regex = r"(\d{1,2}):(\d{1,2}):(\d{1,2}) (am|pm)"
        matches = re.search(regex, timeString, re.IGNORECASE)
        if matches:
            hour = matches.group(1)
            minute = matches.group(2)
            sec = matches.group(3)
            ampm = matches.group(4)
            if ampm.lower() == 'pm':
                hour = int(hour) + 12
            time = dt.time(hour=int(hour), minute=int(minute), second=int(sec))
            return time
        return None

    def parseSun(self):
        if (self.lastUpdatedDay != dt.datetime.now().day) or (self.lastUpdatedDay == None):
            self.lastUpdatedDay = dt.datetime.now().day
            url = 'https://api.sunrise-sunset.org/json?lat=48.7557&lng=21.9184'
            with urllib.request.urlopen(url) as response:
                page = response.read()
            obj = json.loads(page.decode('utf8'))
            today = dt.datetime.today()

            sunrisetime = self.getTimeFromFormat(obj['results']['sunrise'])
            sunsettime = self.getTimeFromFormat(obj['results']['sunset'])

            if (sunsettime is not None and sunsettime is not None):
                utc = pytz.timezone('UTC')
                local_tz = pytz.timezone('Europe/Bratislava')
                todaysunrise = utc.localize(dt.datetime.combine(today, sunrisetime)).astimezone(local_tz)
                todaysunset = utc.localize(dt.datetime.combine(today, sunsettime)).astimezone(local_tz)
                print('sunrise: ')
                print(todaysunrise)
                print('sunset: ')
                print(todaysunset)

                print('sunrise: ', str(todaysunrise.hour))
                print('sunset: ', str(todaysunset.hour))

                self.sunset = todaysunset
                self.sunrise = todaysunrise

    def getSunrise(self):
        return self.sunrise

    def getSunset(self):
        return self.sunset

    def getHladina(self):
        return self.hladina
