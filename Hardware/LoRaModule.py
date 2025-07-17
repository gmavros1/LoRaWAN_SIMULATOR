import copy
import json
from collections import defaultdict

from heapq import nlargest
from typing import Dict, List

from Utils import Computations
from Physics.Environment import Environment
from Wireless.LoRaPacket import LoRaPacket
from Wireless.signals import LoRaWirelessSignal

class Location:
    def __init__(self,x, y):
        self.x = x
        self.y = y


class LoRaModule:
    def __init__(self, id: str, parameters_path: str, position: Location):
        self.ID: str = id
        self.TX_Buffer: list[LoRaPacket] = []
        self.RX_Buffer: list[LoRaPacket] = []
        self.location: Location = position

        parameters: dict
        with open(parameters_path) as f: parameters = json.load(f)

        self.SF: int = parameters["sf"]
        self.Channel: int = parameters["channel"]
        self.Bandwidth: int = parameters["bandwidth"]
        self.PowerTX: float = parameters["PowerTX"]

        self.RSSI7: float = parameters["RSSI_sf7"]
        self.RSSI8: float = parameters["RSSI_sf8"]
        self.RSSI9: float = parameters["RSSI_sf9"]
        self.RSSI10: float = parameters["RSSI_sf10"]
        self.RSSI11: float = parameters["RSSI_sf11"]
        self.RSSI12: float = parameters["RSSI_sf12"]

        # Default
        self.RSSI: float = self.RSSI7

    def generate_packet(self,generation_time: int, payload: dict, header: dict):
        header["source"] = self.ID # Define the source in header
        new_packet = LoRaPacket(generation_time, payload, header, Computations.toa(Computations.compute_payload_size(payload), self.SF))
        self.TX_Buffer.append(new_packet)

    def transmit_packet(self):
        if len(self.TX_Buffer) > 0:
            wireless_lora_signal = LoRaWirelessSignal(self.TX_Buffer.pop(), self)
            if wireless_lora_signal.lora_packet.segment_counter > 1:
                copy_wireless_lora_signal = copy.deepcopy(wireless_lora_signal)
                copy_wireless_lora_signal.lora_packet.segment_counter -= 1
                self.TX_Buffer.append(copy_wireless_lora_signal.lora_packet)
            return wireless_lora_signal
        return None

    def receive_packets_partial(self, environment: Environment):
         packets_in_channel_sf = environment.lora_packet_over_air[self.Channel - 1][self.SF - 7].copy() # To have 1st indexed as 0
         for i in range(len(packets_in_channel_sf)-1, -1, -1):
             rx_power = Computations.calculate_received_power(Computations.distance(
                 packets_in_channel_sf[i].signal.source_location, self.location),
                 packets_in_channel_sf[i].signal.tx_power)

             if rx_power < self.RSSI:
                 del packets_in_channel_sf[i]
                 continue
             else:
                 packets_in_channel_sf[i].signal.rx_power = rx_power

         if len(packets_in_channel_sf) < 1:
             # nothing (or only one pkt) to compare
             return
         elif len(packets_in_channel_sf) == 1:
             self.RX_Buffer.append(packets_in_channel_sf[0].signal.lora_packet)
             if packets_in_channel_sf[0].toa_left == 0:
                 self.decode_packet(packets_in_channel_sf[0].signal.time_over_air_required)
         else:
             top_two = nlargest(2, packets_in_channel_sf, key=lambda p: p.signal.rx_power)

             # capture effect (“capture margin” 6 dB)
             if top_two[0].signal.rx_power - top_two[1].signal.rx_power >= 6:
                 self.RX_Buffer.append(top_two[0].signal.lora_packet)
                 if top_two[0].toa_left == 0:
                    self.decode_packet(top_two[0].signal.time_over_air_required)


    def decode_packet(self, segments_required):
        buckets: Dict[str, List[LoRaPacket]] = defaultdict(list)
        for pkt in self.RX_Buffer:
            buckets[pkt.ID].append(pkt)
        print(dict(buckets))

        for pkt in dict(buckets).values():
            if segments_required - 1 < len(pkt) < segments_required + 1:
                self.TX_Buffer.append(pkt) # STORE FOR FORWARD
                print("SUCCESSFULLY DECODED")
            else:
                print("DECODING ERROR")

        self.RX_Buffer = []
        print(self.TX_Buffer)
