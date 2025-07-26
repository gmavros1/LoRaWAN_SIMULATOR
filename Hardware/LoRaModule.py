import copy
import json
from collections import defaultdict
from heapq import nlargest
from typing import Dict, List
import Hardware.EVENTS
from Utils import Computations
from Physics.Environment import Environment
from Wireless.LoRaPacket import LoRaPacket
from Wireless.signals import LoRaWirelessSignal

class Location:
    def __init__(self,x, y):
        self.x = x
        self.y = y


def sleep():
    # print("SLEEP")
    return None, None


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

        self.RSSIs = {"7": parameters["RSSI_sf7"],
                 "8": parameters["RSSI_sf8"],
                 "9": parameters["RSSI_sf9"],
                 "10": parameters["RSSI_sf10"],
                 "11": parameters["RSSI_sf11"],
                 "12": parameters["RSSI_sf12"]}

        # Default
        self.RSSI: float = self.RSSIs["7"]
        self.counter = None

        # LOGS
        self.generated_packets: int = 0
        self.successfully_received_packets = []

    def tick(self):
        if self.counter > 0: self.counter -= 1

    def generate_packet(self,generation_time: int, payload: dict, header: dict):
        header["source"] = self.ID # Define the source in header
        new_packet: LoRaPacket = LoRaPacket(generation_time, payload, header, Computations.toa(Computations.compute_payload_size(payload), self.SF))
        new_packet.IsFirstPacket = True
        new_packet.sf = self.SF
        new_packet.channel = self.Channel
        self.TX_Buffer.append(new_packet)

        # Statistics
        self.generated_packets += 1

        # print("GENERATE PACKET")
        return Hardware.EVENTS.ClassA.GENERATE_PACKET, None

    def transmit_packet(self):
        # print("TRANSMIT PACKET")
        if len(self.TX_Buffer) > 0:
            wireless_lora_signal = LoRaWirelessSignal(self.TX_Buffer.pop(), self)
            if wireless_lora_signal.lora_packet.segment_counter > 1:
                copy_wireless_lora_signal = copy.deepcopy(wireless_lora_signal)
                copy_wireless_lora_signal.lora_packet.segment_counter -= 1
                copy_wireless_lora_signal.lora_packet.IsFirstPacket = False
                self.TX_Buffer.append(copy_wireless_lora_signal.lora_packet)
            else:
                return Hardware.EVENTS.ClassA.TRANSMISSION_END, wireless_lora_signal

            # Return Packet and Event
            if wireless_lora_signal.lora_packet.IsFirstPacket:
                return Hardware.EVENTS.ClassA.TRANSMISSION_START, wireless_lora_signal
            else:
                return None, wireless_lora_signal
        return None, None

    def clear_receiver_from_interrupted_packets(self):
        # remove / drop every packet that uses *this* node’s channel & SF
        self.RX_Buffer[:] = [
            pkt for pkt in self.RX_Buffer
            if not (pkt.sf == self.SF and pkt.channel == self.Channel)
        ]

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
             # nothing to compare
             return None, None
         elif len(packets_in_channel_sf) == 1:
             if packets_in_channel_sf[0].signal.lora_packet.IsFirstPacket: # Receiving first segment of packet
                self.clear_receiver_from_interrupted_packets()                                        # All the previous stored has no effect
                # print("RECEPTION START")
             self.RX_Buffer.append(packets_in_channel_sf[0].signal.lora_packet)
             if packets_in_channel_sf[0].toa_left == 0:
                    return self.decode_packet(packets_in_channel_sf[0].signal.time_over_air_required)
             elif packets_in_channel_sf[0].signal.lora_packet.IsFirstPacket:
                 return Hardware.EVENTS.ClassA.RECEIVE_START, None
             else:
                 return None, None

         else:
             top_two = nlargest(2, packets_in_channel_sf, key=lambda p: p.signal.rx_power)

             # capture effect (“capture margin” 6 dB)
             if top_two[0].signal.rx_power - top_two[1].signal.rx_power >= 6: ## Activate ro deactivate capture effect
                 if top_two[0].signal.lora_packet.IsFirstPacket:  # Receiving first segment of packet
                     self.clear_receiver_from_interrupted_packets()
                     # print("RECEPTION START")
                 self.RX_Buffer.append(top_two[0].signal.lora_packet)
                 if top_two[0].toa_left == 0:
                    return self.decode_packet(top_two[0].signal.time_over_air_required)
                 elif top_two[0].signal.lora_packet.IsFirstPacket:
                     return Hardware.EVENTS.ClassA.RECEIVE_START, None
                 else:
                     return None, None
             return None, None


    def decode_packet(self, segments_required):
        buckets: Dict[str, List[LoRaPacket]] = defaultdict(list)
        for pkt in [
            pkt for pkt in self.RX_Buffer
            if (pkt.sf == self.SF and pkt.channel == self.Channel)
        ]:
            buckets[pkt.ID].append(pkt)
        # print(dict(buckets))

        for pkt in dict(buckets).values():
            if segments_required - 1 < len(pkt) < segments_required + 1:
                self.TX_Buffer.append(pkt) # STORE FOR FORWARD
                # self.RX_Buffer = []
                # print("SUCCESSFULLY DECODED")
                # print("RECEPTION END")

                # Statistics
                self.successfully_received_packets.append(pkt[0].ID)

                return Hardware.EVENTS.ClassA.PACKET_DECODED, None
            else:
                # self.RX_Buffer = []
                # print("DECODING ERROR")
                # print("RECEPTION END")
                return Hardware.EVENTS.ClassA.PACKET_NON_DECODED, None

    # For Example for RX1 and RX2 like Delays
    def sleep_delay(self, time: int):
        if self.counter == None:
            self.counter = time
            self.counter -= 1
            return Hardware.EVENTS.ClassA.DELAY_START, None

        if self.counter == 1:
            self.counter = None
            return Hardware.EVENTS.ClassA.DELAY_END, None

        self.counter -= 1
        return None, None

