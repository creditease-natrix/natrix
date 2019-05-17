
try:
    import ConfigParser as configparser
except ImportError:
    import configparser


class NatrixConfig(configparser.ConfigParser):
    def __init__(self, defaults=None):
        configparser.ConfigParser.__init__(self, defaults=None)

    def optionxform(self, optionstr):
        return optionstr


conf = configparser.ConfigParser()
