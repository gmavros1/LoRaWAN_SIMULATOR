import Hardware.EVENTS
import Physics.Environment
import Utils.TrafficModel
import Wireless.signals
from Hardware.LoRaModule import sleep
from Hardware.SensorNode import SensorNode

MAXIMUM_PARALLEL_PACKETS = 8

class LoRaWANGateway(SensorNode):

    def __init__(self, node_id: str, wurx_json: str, lora_json: str, position: Wireless.signals.Location, environment, NetworkServer):
        super().__init__(node_id, wurx_json, lora_json, position)
        self.action.executable, self.action.args = self.multiple_input, [environment]
        self.NetworkServer = NetworkServer

    def transmit_delay_1(self):
        # print("RX DELAY 1")
        # Standard 1 s
        signal, _ = self.lora.sleep_delay(self.RECEIVE_DELAY_1)
        if signal == Hardware.EVENTS.ClassA.DELAY_START:
            return Hardware.EVENTS.ClassA.RX1_DELAY_START, None
        elif signal == Hardware.EVENTS.ClassA.DELAY_END:
            return Hardware.EVENTS.ClassA.RX1_DELAY_END, None
        else:
            return None, None

    def multiple_input(self, environment):
        # FIND OCCUPIED RESOURCES SF/CHANNEL
        sf_channel = [(i, j) for i, row  in enumerate(environment.lora_packet_over_air) for j, cell in enumerate(row) if cell] # non-empty test

        for i in range(MAXIMUM_PARALLEL_PACKETS):
            if i == len(sf_channel):
                break

            self.lora.Channel = sf_channel[i][0] + 1
            self.lora.SF = sf_channel[i][1] + 7
            self.lora.RSSI = self.lora.RSSIs[str(self.lora.SF)]

            self.lora.receive_packets_partial(environment)

        return None, None

    def suggest_sf(self, rx_power_dbm):
        # Ordered from highest to lowest spreading factor
        sf_thresholds = {
            12: self.lora.RSSIs["12"],
            11: self.lora.RSSIs["11"],
            10: self.lora.RSSIs["10"],
            9: self.lora.RSSIs["9"],
            8: self.lora.RSSIs["8"],
            7: self.lora.RSSIs["7"]
        }
        for sf, sensitivity in sorted(sf_thresholds.items()):
            if rx_power_dbm >= sensitivity:
                return sf
        return None  # No suitable SF

    def generate_accept_packet(self, time):
        received_join_request = self.lora.TX_Buffer.pop()
        payload = {"control": "JOIN_ACCEPT", "SF": self.suggest_sf(received_join_request.received_power)}
        header = {"destination": "00000"}

        self.lora.generate_packet(time, payload, header)
        self.lora.TX_Buffer[-1].Destination = received_join_request.Source
        return Hardware.EVENTS.ClassA.GENERATE_PACKET, None

    def protocol_driver(self, interrupt: Hardware.EVENTS.ClassA, time: int,
                        environment: Physics.Environment.Environment):

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

    # FOR OTAA PROCESS
    # Join Request -> 18 bytes
    # Join Accept and Join Requests Delay set at 5 and 6 sec for RX1 AND RX2 DELAY
    # Join Accept -> 12 + 16 bytes
    def join_driver(self, interrupt: Hardware.EVENTS.ClassA, time: int,
                        environment: Physics.Environment.Environment):

        if self.action.executable == self.multiple_input and self.lora.TX_Buffer:
            self.action.executable, self.action.args = self.transmit_delay_1, []

        if self.action.executable == self.transmit_delay_1 and interrupt == Hardware.EVENTS.ClassA.RX1_DELAY_END:
            self.action.executable, self.action.args = self.generate_accept_packet, [time]

        if self.action.executable == self.generate_accept_packet and interrupt == Hardware.EVENTS.ClassA.GENERATE_PACKET:
            self.action.executable, self.action.args = self.lora.transmit_packet, []

        if self.action.executable == self.lora.transmit_packet and interrupt == Hardware.EVENTS.ClassA.TRANSMISSION_END:
            self.action.executable, self.action.args = self.multiple_input, [environment]