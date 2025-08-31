import Hardware.EVENTS
import Physics.Environment
import Utils.TrafficModel
import Utils.Computations as cmp
import Wireless.signals
from Hardware.LoRaModule import sleep
from Hardware.SensorNode import SensorNode
import random

class LoRaWANNode(SensorNode):

    def __init__(self, node_id: str, wurx_json: str, lora_json: str, position: Wireless.signals.Location):
        super().__init__(node_id, wurx_json, lora_json, position)
        self.event_generator: Utils.TrafficModel.TrafficModel = Utils.TrafficModel.TrafficModel()
        self.action.executable, self.action.args = sleep, []

    def receive_delay_1(self):
        # print("RX DELAY 1")
        time: int = self.RECEIVE_DELAY_1 # Standard 5 in joining process
        signal, _ = self.lora.sleep_delay(time)
        if signal == Hardware.EVENTS.ClassA.DELAY_START:
            return Hardware.EVENTS.ClassA.RX1_DELAY_START, None
        elif signal == Hardware.EVENTS.ClassA.DELAY_END:
            return Hardware.EVENTS.ClassA.RX1_DELAY_END, None
        else:
            return None, None

    def contention_window_delay(self):
        # print("RX DELAY 1")
        time: int = Utils.Computations.spaced_delay_from_id(self.lora.ID) # contention delay initialized to 50 sec
        signal, _ = self.lora.sleep_delay(time)
        if signal == Hardware.EVENTS.ClassA.DELAY_START:
            return Hardware.EVENTS.ClassA.CONTENTION_WINDOW_START, None
        elif signal == Hardware.EVENTS.ClassA.DELAY_END:
            return Hardware.EVENTS.ClassA.CONTENTION_WINDOW_END, None
        else:
            return None, None

    def receive_delay_2(self):
        # print("RX DELAY 2")
        time:int =  self.RECEIVE_DELAY_2 # Standard 6 sc (+ RECEIVE_DELAY_1)
        signal, _ = self.lora.sleep_delay(time)
        if signal == Hardware.EVENTS.ClassA.DELAY_START:
            return Hardware.EVENTS.ClassA.RX2_DELAY_START, None
        elif signal == Hardware.EVENTS.ClassA.DELAY_END:
            return Hardware.EVENTS.ClassA.RX2_DELAY_END, None
        else:
            return None, None

    def rx_1(self, environment):
        # print("RX 1")
        timeout = int(cmp.preamble_time(self.lora.SF))
        signal_timer, _ = self.lora.sleep_delay(timeout) # Used as timer
        signal_receiver, _ = self.lora.receive_packets_partial(environment)
        if signal_timer == Hardware.EVENTS.ClassA.DELAY_START and signal_receiver == None:
            return Hardware.EVENTS.ClassA.RX1_START, None
        elif signal_timer == Hardware.EVENTS.ClassA.DELAY_END and not self.lora.RX_Buffer: # No reception, end of time
            return Hardware.EVENTS.ClassA.RX1_END, None
        else:
            if self.lora.RX_Buffer:
                self.lora.counter = None # Now it doesn't depend on time
            return signal_receiver, None

    def rx_2(self, environment):
        # print("RX 2")
        timeout = int(cmp.preamble_time(self.lora.SF))
        signal_timer, _ = self.lora.sleep_delay(timeout) # Used as timer
        signal_receiver, _ = self.lora.receive_packets_partial(environment)
        if signal_timer == Hardware.EVENTS.ClassA.DELAY_START and signal_receiver == None:
            return Hardware.EVENTS.ClassA.RX2_START, None
        elif signal_timer == Hardware.EVENTS.ClassA.DELAY_END and not self.lora.RX_Buffer: # No reception, end of time
            return Hardware.EVENTS.ClassA.RX2_END, None
        else:
            if self.lora.RX_Buffer:
                self.lora.counter = None # Now it doesn't depend on time
            return signal_receiver, None

    def join_packet_generation(self, time):
        payload = {"control": "JOIN_REQUEST", "PADDING": "000DD0"}
        header = {"destination": "00000"}
        return self.lora.generate_packet(time, payload, header)

    def decode_join_accept(self):
        if self.lora.TX_Buffer:
            packet_received = self.lora.TX_Buffer.pop()
            if packet_received.Payload["control"] == "JOIN_ACCEPT" and packet_received.Destination == self.lora.ID:
                # successfully joined the network
                self.joined_to_network = True
                print(self.lora.ID + " DONE")
                self.lora.SF = packet_received.Payload["SF"]
                return Hardware.EVENTS.ClassA.JOIN_ACCEPT_SUCCESS, None

        return Hardware.EVENTS.ClassA.JOIN_ACCEPT_FAILED, None

    def protocol_driver(self, interrupt: Hardware.EVENTS.ClassA, time: int,
                        environment: Physics.Environment.Environment):

        if self.action.executable == sleep and self.event_generator.event_happened():
                payload = {"messages": "DUMMY"}
                header = {"destination": "00000"}
                self.action.executable, self.action.args = self.lora.generate_packet, [time, payload, header]

        if self.action.executable == self.lora.generate_packet and interrupt == Hardware.EVENTS.ClassA.GENERATE_PACKET:
            self.action.executable, self.action.args = self.lora.transmit_packet, []

        if self.receiving_windows_enabled:
            if self.action.executable == self.lora.transmit_packet and interrupt == Hardware.EVENTS.ClassA.TRANSMISSION_END:
                self.action.executable, self.action.args = self.receive_delay_1, []

            if self.action.executable == self.receive_delay_1 and interrupt == Hardware.EVENTS.ClassA.RX1_DELAY_END:
                self.action.executable, self.action.args = self.rx_1, [environment]

            if self.action.executable == self.rx_1 and interrupt == Hardware.EVENTS.ClassA.PACKET_DECODED:
                self.action.executable, self.action.args = sleep, []

            if self.action.executable == self.rx_1 and (interrupt == Hardware.EVENTS.ClassA.RX1_END or interrupt == Hardware.EVENTS.ClassA.PACKET_NON_DECODED):
                self.action.executable, self.action.args = self.receive_delay_2, []

            if self.action.executable == self.receive_delay_2 and interrupt == Hardware.EVENTS.ClassA.RX2_DELAY_END:
                self.action.executable, self.action.args = self.rx_2, [environment]

            if self.action.executable == self.rx_2 and (interrupt == Hardware.EVENTS.ClassA.PACKET_DECODED or
                                                        interrupt == Hardware.EVENTS.ClassA.PACKET_NON_DECODED or
                                                        interrupt == Hardware.EVENTS.ClassA.RX2_END):
                self.action.executable, self.action.args = sleep, []
        else:
            if self.action.executable == self.lora.transmit_packet and interrupt == Hardware.EVENTS.ClassA.TRANSMISSION_END:
                self.action.executable, self.action.args = sleep, []

    def join_driver(self, interrupt: Hardware.EVENTS.ClassA, time: int,
                        environment: Physics.Environment.Environment):

        if self.action.executable == sleep and not self.joined_to_network:
            self.action.executable, self.action.args = self.lora.sleep_delay, [Utils.Computations.spaced_delay_from_id(self.lora.ID)]

        # Send Join Request - 18 bytes
        if self.action.executable == self.lora.sleep_delay and interrupt == Hardware.EVENTS.ClassA.DELAY_END:
            self.action.executable, self.action.args = self.join_packet_generation, [time]

        if self.action.executable == self.join_packet_generation and interrupt == Hardware.EVENTS.ClassA.GENERATE_PACKET:
            self.action.executable, self.action.args = self.lora.transmit_packet, []

        # Wait for 5 sec and start receiving
        if self.action.executable == self.lora.transmit_packet and interrupt == Hardware.EVENTS.ClassA.TRANSMISSION_END:
            self.action.executable, self.action.args = self.receive_delay_1, []

        if self.action.executable == self.receive_delay_1 and interrupt == Hardware.EVENTS.ClassA.RX1_DELAY_END:
            self.action.executable, self.action.args = self.rx_1, [environment]

        # RECEIVING AT RX1 THE JOIN ACCEPT
        if self.action.executable == self.rx_1 and interrupt == Hardware.EVENTS.ClassA.PACKET_DECODED:
            self.action.executable, self.action.args = self.decode_join_accept, []

        # If not received wait 1 sec
        if self.action.executable == self.rx_1 and (
                interrupt == Hardware.EVENTS.ClassA.RX1_END or interrupt == Hardware.EVENTS.ClassA.PACKET_NON_DECODED):
            self.action.executable, self.action.args = self.receive_delay_2, []
            self.lora.clear_receiver_from_interrupted_packets()

        if self.action.executable == self.receive_delay_2 and interrupt == Hardware.EVENTS.ClassA.RX2_DELAY_END:
            self.action.executable, self.action.args = self.rx_2, [environment]

        # CHECK FOR RECEIVED PACKETS AFTER RX2
        if self.action.executable == self.rx_2 and (interrupt == Hardware.EVENTS.ClassA.PACKET_DECODED or
                                                    interrupt == Hardware.EVENTS.ClassA.PACKET_NON_DECODED or
                                                    interrupt == Hardware.EVENTS.ClassA.RX2_END):
            self.action.executable, self.action.args = self.decode_join_accept, []

        # If received add gateway
        # Change sf according to gateways suggestions
        if self.action.executable == self.decode_join_accept and interrupt == Hardware.EVENTS.ClassA.JOIN_ACCEPT_SUCCESS:
            self.action.executable, self.action.args = sleep, []
        elif self.action.executable == self.decode_join_accept and interrupt == Hardware.EVENTS.ClassA.JOIN_ACCEPT_FAILED:
            self.action.executable, self.action.args = self.contention_window_delay, []
            self.lora.clear_receiver_from_interrupted_packets()

        # Again after contention window
        if self.action.executable == self.contention_window_delay and interrupt == Hardware.EVENTS.ClassA.CONTENTION_WINDOW_END:
            self.action.executable, self.action.args = self.join_packet_generation, [time]
