import json
from LoRaPacket import LoRaPacket
from WirelessSignal import WirelessSignal

class Location:
    def __init__(self,x, y):
        self.x = x
        self.y = y


class LoRaModule:
    def __init__(self, id: str, parameters_path: str, position: Location):
        self.ID: str = id
        self.TX_Buffer = [LoRaPacket]
        self.RX_Buffer = [LoRaPacket]
        self.location: Location = position

        parameters: dict
        with open(parameters_path) as f: parameters = json.load(f)

        self.SF: int = parameters["sf"]
        self.Channel: int = parameters["channel"]
        self.Bandwidth: int = parameters["bandwidth"]
        self.PowerTX: float = parameters["PowerTX"]
        self.RSSI: float = parameters["RSSI"]

    def generate_packet(self,generation_time: int, payload: dict, header: dict):
        header["source"] = self.ID # Define the source in header
        new_packet = LoRaPacket(generation_time, payload, header)
        self.TX_Buffer.append(new_packet)

    def transmit_packet(self):
        wireless_lora_signal = WirelessSignal(self.TX_Buffer.pop(), self)
        return wireless_lora_signal


