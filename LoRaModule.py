import json


class LoRaModule:
    def __init__(self, id: int, parameters_path: str):
        self.ID = id

        parameters: dict
        with open(parameters_path) as f: parameters = json.load(f)

        self.SF = parameters["sf"]
        self.Channel = parameters["channel"]
        self.Bandwidth = parameters["bandwidth"]
        self.PowerTX = parameters["PowerTX"]
        self.RSSI = parameters["RSSI"]

