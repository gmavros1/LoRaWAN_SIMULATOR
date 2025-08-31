import Hardware.EVENTS
import Physics.Environment
import Utils.TrafficModel
import Utils.Computations as cmp
import Wireless.signals
from Hardware.LoRaModule import sleep
from Hardware.SensorNode import SensorNode
import random

class Multihop1Node(SensorNode):

    def __init__(self, node_id: str, wurx_json: str, lora_json: str, position: Wireless.signals.Location):
        super().__init__(node_id, wurx_json, lora_json, position)
        self.event_generator: Utils.TrafficModel.TrafficModel = Utils.TrafficModel.TrafficModel()
        self.action.executable, self.action.args = sleep, []

    def join_driver(self, interrupt: Hardware.EVENTS.ClassA, time: int,
                        environment: Physics.Environment.Environment):

        if self.action.executable == sleep and not self.joined_to_network:
            self.action.executable, self.action.args = self.lora.sleep_delay, [Utils.Computations.spaced_delay_from_id(self.lora.ID)]


