from Controller import Controller
from Logger import Logger

app = Controller({
    'fan': 6,
    'light': 5,
    'pir': 7,
    'maxFanTime': 60,
    'lowBatteryLightTime': 60,
    'medBatteryLightTime': 180,
    'highBatteryLightTime': 300,
    'spiMosi': 24,
    'spiMiso': 23,
    'spiClk': 18,
    'spiCs': 25,
    'battVoltageCh': 5,
    'battCurrentCh': 7,
    'solarCurrentCh': 6,
    'avgFor': 60,
    'sleepFor': 1
})

app.setLogger(Logger('%d.%m.%Y %H:%M:%S'))
app.run()
