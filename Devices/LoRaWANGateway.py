import Hardware.EVENTS
import Physics.Environment
import Utils.TrafficModel
import Wireless.signals
from Hardware.LoRaModule import sleep
from Hardware.SensorNode import SensorNode

class LoRaWANGateway(SensorNode):

    def __init__(self, node_id: str, wurx_json: str, lora_json: str, position: Wireless.signals.Location, environment):
        super().__init__(node_id, wurx_json, lora_json, position)
        self.action.executable, self.action.args = self.multiple_input, [environment]
        self.downlink_delay_after_reception: int = 20

    def transmit_delay_1(self):
        print("RX DELAY 1")
        # Standard 1 s
        signal, _ = self.lora.sleep_delay(self.downlink_delay_after_reception)
        if signal == Hardware.EVENTS.ClassA.DELAY_START:
            return Hardware.EVENTS.ClassA.RX1_DELAY_START, None
        elif signal == Hardware.EVENTS.ClassA.DELAY_END:
            return Hardware.EVENTS.ClassA.RX1_DELAY_END, None
        else:
            return None, None

    def multiple_input(self, environment):
        MAXIMUM_PARALLEL_PACKETS = 8

        # FIND OCCUPIED RESOURCES SF/CHANNEL
        sf_channel = [(i, j) for i, row  in enumerate(environment.lora_packet_over_air) for j, cell in enumerate(row) if cell] # non-empty test

        for i in range(MAXIMUM_PARALLEL_PACKETS):
            if i == len(sf_channel):
                break

            self.lora.Channel = sf_channel[i][0] + 1
            self.lora.SF = sf_channel[i][1] + 7

            self.lora.receive_packets_partial(environment)

        return None, None

    def protocol_driver(self, interrupt: Hardware.EVENTS.ClassA, time: int,
                        environment: Physics.Environment.Environment, wireless_signal):

        pass
        # ACK LoRaWAN - Optional should be avoided
        # Not full duplex
        # https://www.thethingsnetwork.org/docs/lorawan/limitations/?utm_source=chatgpt.com
        # if self.action.executable == self.lora.receive_packets_partial and interrupt == Hardware.EVENTS.ClassA.PACKET_DECODED:
        #     self.action.executable, self.action.args = self.transmit_delay_1, []
        #
        # if self.action.executable == self.transmit_delay_1 and interrupt == Hardware.EVENTS.ClassA.RX1_DELAY_END:
        #     payload = {"messages": "ACK"}
        #     header = {"destination": "00000"}
        #     self.action.executable, self.action.args = self.lora.generate_packet, [time, payload, header]
        #
        # if self.action.executable == self.lora.generate_packet and interrupt == Hardware.EVENTS.ClassA.GENERATE_PACKET:
        #     self.action.executable, self.action.args = self.lora.transmit_packet, []
        #
        # if self.action.executable == self.lora.transmit_packet and interrupt == Hardware.EVENTS.ClassA.TRANSMISSION_END:
        #     self.action.executable, self.action.args = self.lora.receive_packets_partial, [environment]
