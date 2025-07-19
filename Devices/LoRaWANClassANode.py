import Hardware.EVENTS
import Physics.Environment
import Utils.TrafficModel
import Wireless.signals
from Hardware.LoRaModule import sleep
from Hardware.SensorNode import SensorNode

class LoRaWANNode(SensorNode):

    def __init__(self, node_id: str, wurx_json: str, lora_json: str, position: Wireless.signals.Location):
        super().__init__(node_id, wurx_json, lora_json, position)
        self.EVENT: Hardware.EVENTS.ClassA
        self.event_generator: Utils.TrafficModel.TrafficModel = Utils.TrafficModel.TrafficModel()
        self.action.executable, self.action.args = sleep, []

    def protocol_driver(self, interrupt: Hardware.EVENTS.ClassA, time: int,
                        environment: Physics.Environment.Environment, wireless_signal):

        if self.action.executable == sleep and self.event_generator.event_happened():
                payload = {"messages": "DUMMY"}
                header = {"destination": "00000"}
                self.action.executable, self.action.args = self.lora.generate_packet, [time, payload, header]

        if self.action.executable == self.lora.generate_packet and interrupt == Hardware.EVENTS.ClassA.GENERATE_PACKET:
            self.action.executable, self.action.args = self.lora.transmit_packet, []

        if self.action.executable == self.lora.transmit_packet and interrupt == Hardware.EVENTS.ClassA.TRANSMISSION_END:
            self.action.executable, self.action.args = sleep, []









