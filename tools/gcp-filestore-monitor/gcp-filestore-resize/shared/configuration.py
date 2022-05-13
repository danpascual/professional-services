import json

class Configuration(object):
    @staticmethod
    def get_configuration():
        result = {}
        with open('config.json') as config_file:
            result = json.load(config_file)
        return result