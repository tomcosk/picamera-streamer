import configparser

class Config():

    def __init__(self, filename):
        self.config = configparser.ConfigParser()
        self.config.read(filename)
        self.filename = filename


    def write(self):
        with open(filename, 'w') as configfile:
            config.write(configfile)

    def reload(self):
        self.config = config.read(filename)

    def getValue(self, section, property):
        return self.config.get(section,property)

    def setValue(self, section, property, value):
        self.config[section][property] = value
