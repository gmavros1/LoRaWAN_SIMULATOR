import Hardware.EVENTS
import Physics.Environment
import Utils.TrafficModel
import Wireless.signals
from Hardware.LoRaModule import sleep
from Hardware.SensorNode import SensorNode

class LoRaWANGateway(SensorNode):

    def __init__(self, node_id: str, wurx_json: str, lora_json: str, position: Wireless.signals.Location, environment):
        super().__init__(node_id, wurx_json, lora_json, position)
        self.EVENT: Hardware.EVENTS.ClassA
        # self.event_generator: Utils.TrafficModel.TrafficModel = Utils.TrafficModel.TrafficModel()
        self.action.executable, self.action.args = self.lora.receive_packets_partial, [environment]

    def protocol_driver(self, interrupt: Hardware.EVENTS.ClassA, time: int,
                        environment: Physics.Environment.Environment, wireless_signal):

        if self.action.executable == self.lora.receive_packets_partial:
            self.action.executable, self.action.args = self.lora.receive_packets_partial, [environment]