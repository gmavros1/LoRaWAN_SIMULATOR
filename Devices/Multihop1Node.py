import Hardware.EVENTS
import Physics.Environment
import Utils.TrafficModel
import Utils.Computations as cmp
import Wireless.signals
from Hardware.LoRaModule import sleep
# from Hardware.SensorNode import SensorNode
from Devices.LoRaWANClassANode import LoRaWANNode
from Wireless.LoRaPacket import LoRaPacket
import random

class Multihop1Node(LoRaWANNode):

    def __init__(self, node_id: str, wurx_json: str, lora_json: str, position: Wireless.signals.Location):
        super().__init__(node_id, wurx_json, lora_json, position)
        self.event_generator: Utils.TrafficModel.TrafficModel = Utils.TrafficModel.TrafficModel()
        self.action.executable, self.action.args = sleep, []

        # PROTOCOL RELATED INFORMATION
        self.cluster_channel: int = -1 # -1 Indicates that it is not assigned to a cluster
        self.relay_node:str = ""
        self.hop_depth:int = -1

    def idle_listening_with_timeout(self, timeout, environment):
        pass


    """
        A node which has been already assigned, Idle listens and waiting for join Requests.
        After every joins accept response, sleep and repeats the process. 
        Here C_CHANNEL and hop_depth are included in the payload.
    """
    def waiting_for_join_requests(self, environment, time):
        # timeout = 60000 # Time waiting to receive join accept answers
        # signal_timer, _ = self.lora.sleep_delay(timeout)  # Used as timer
        # signal_receiver, _ = self.lora.receive_packets_partial(environment)
        #
        # # See if there is any join request packet
        # if signal_receiver == Hardware.EVENTS.ClassA.PACKET_DECODED:
        #     received_packet: LoRaPacket = self.lora.TX_Buffer.pop()
        #     # If wur communication could be established
        #     if received_packet.received_power >= self.wurx.Sensitivity_dBm:
        #         payload = {"control": "JOIN_ACCEPT", "c_channel": self.cluster_channel, "h_depth": self.hop_depth + 1}
        #         header = {"destination": "00000"}
        #
        #         self.lora.generate_packet(time, payload, header)
        #         self.lora.TX_Buffer[-1].Destination = received_packet.Source
        #
        #         # If packet is correct send packet.decoded to send join_accept after sensing
        #         # if not do not send anything. It will remain to hear
        # else:
        #
        #
        # if signal_timer == Hardware.EVENTS.ClassA.DELAY_END:
        #     return None, signal_timer
        return None, None


    """
        A node (already assigned), or a gw has been respond with a JOIN_ACCEPT.
        PAYLOAD SHOULD CONTAIN COMMUNICATION CHANNEL (cluster_channel). SRC id should be used as relay node ID.
        If node, it means that the node is close enough to communicate with wur radio. This is checked during
        the JOIN_ACCEPT packet construction from the relay node.
        Hop-depth information also is stored - contained in packet payload.
    """
    def decode_join_accept(self):
        if self.lora.TX_Buffer:
            packet_received = self.lora.TX_Buffer.pop()
            if packet_received.Payload["control"] == "JOIN_ACCEPT" and packet_received.Destination == self.lora.ID:
                # successfully joined the network
                self.joined_to_network = True
                self.cluster_channel = int(packet_received.Payload["c_channel"])
                self.hop_depth = int(packet_received.Payload["h_depth"])
                self.relay_node = packet_received.Source
                print(self.lora.ID + " DONE")
                return Hardware.EVENTS.ClassA.JOIN_ACCEPT_SUCCESS, None
        return Hardware.EVENTS.ClassA.JOIN_ACCEPT_FAILED, None


    def protocol_driver(self, interrupt: Hardware.EVENTS.ClassA, time: int,
                        environment: Physics.Environment.Environment):
        pass

    def join_driver(self, interrupt: Hardware.EVENTS.ClassA, time: int,
                        environment: Physics.Environment.Environment):

        """
                BEFORE BEING ASSIGNED TO A NODE OR GATEWAY
        """

        if self.action.executable == sleep and not self.joined_to_network:
            self.action.executable, self.action.args = self.lora.sleep_delay, [Utils.Computations.spaced_delay_from_id(self.lora.ID)]

        # Send Join Request
        if self.action.executable == self.lora.sleep_delay and interrupt == Hardware.EVENTS.ClassA.DELAY_END and not self.joined_to_network:
            self.action.executable, self.action.args = self.join_packet_generation, [time]

        if self.action.executable == self.join_packet_generation and interrupt == Hardware.EVENTS.ClassA.GENERATE_PACKET:
            self.action.executable, self.action.args = self.lora.transmit_packet, []

        # Start listening and receiving - timeouts in one minute
        if self.action.executable == self.lora.transmit_packet and interrupt == Hardware.EVENTS.ClassA.TRANSMISSION_END:
            self.action.executable, self.action.args = self.receive_delay_1, []

        if self.action.executable == self.receive_delay_1 and interrupt == Hardware.EVENTS.ClassA.RX1_DELAY_END:
            self.action.executable, self.action.args = self.rx_1, [environment]

        # RECEIVING AT RX1 THE JOIN ACCEPT
        if self.action.executable == self.rx_1 and interrupt == Hardware.EVENTS.ClassA.PACKET_DECODED:
            self.action.executable, self.action.args = self.decode_join_accept, []

        # If received packet but not a join accept one
        if self.action.executable == self.decode_join_accept and interrupt == Hardware.EVENTS.ClassA.JOIN_ACCEPT_FAILED:
            self.action.executable, self.action.args = self.contention_window_delay, []
            self.lora.clear_receiver_from_interrupted_packets()
            self.lora.TX_Buffer = [] # CLEAR DECODED PACKETS

        # If not received wait 1 sec
        if self.action.executable == self.rx_1 and (
                interrupt == Hardware.EVENTS.ClassA.RX1_END or
                interrupt == Hardware.EVENTS.ClassA.PACKET_NON_DECODED):
            self.action.executable, self.action.args = self.contention_window_delay, []
            self.lora.clear_receiver_from_interrupted_packets()

        # Again after contention window
        # Goes again to join request
        if self.action.executable == self.contention_window_delay and interrupt == Hardware.EVENTS.ClassA.CONTENTION_WINDOW_END:
            self.action.executable, self.action.args = self.join_packet_generation, [time]

        """
                AFTER BEING ASSIGNED TO A NODE OR GATEWAY
        """

        # If node has received successfully a join accept
        # Wait 10 ms and start idle listening
        if self.action.executable == self.decode_join_accept and interrupt == Hardware.EVENTS.ClassA.JOIN_ACCEPT_SUCCESS:
            self.action.executable, self.action.args = self.lora.sleep_delay, [10]

        # Open Receiver for 4 mins timeout limit
        if self.action.executable == self.lora.sleep_delay and interrupt == Hardware.EVENTS.ClassA.DELAY_END and self.joined_to_network:
            self.action.executable, self.action.args = self.waiting_for_join_requests, [environment, time]

