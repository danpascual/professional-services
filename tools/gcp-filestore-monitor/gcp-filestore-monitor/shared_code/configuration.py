import json

class Configuration(object):
    @staticmethod
    def get_configuration() -> dict:
        result = {}
        with open('config.json') as config_file:
            result = json.load(config_file)
        return result

    def adjust_tier_max_capacity(tier_config: dict, tier_name: str, max_capacity:int):
        if max_capacity == 0:
            return

        enterprise_settings = next(tier for tier in tier_config if tier_name in tier["name"])
        if not enterprise_settings:
            return
        
        enterprise_settings["max_capacity_gb"]=max_capacity