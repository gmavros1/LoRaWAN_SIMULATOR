import Hardware.EVENTS
import Utils.TrafficModel
from Hardware import SensorNode

class LoRaWANNode(SensorNode):

    def __init__(self):
        self.counter = 0
        self.EVENT: Hardware.EVENTS.ClassA
        self.event_generator: Utils.TrafficModel.TrafficModel = Utils.TrafficModel.TrafficModel()
        self.current_state: str = "SLEEP"

    def tick(self):
        if self.counter > 0: self.counter -= 1

    # For RX1 and RX2 Delays
    def sleep_delay(self, time: int):
        if self.counter == 0:
            self.counter = time
            self.counter -= 1
            return Hardware.EVENTS.ClassA.DELAY_START

        if self.counter == 0:
            return Hardware.EVENTS.ClassA.DELAY_END

        self.counter -= 1
        return None

    def protocol_driver(self, signal: Hardware.EVENTS.ClassA):
        if self.current_state == "SLEEP":
            if not self.event_generator.event_happened():
                pass
            else:
                self.current_state = "GENERATE PACKET"

        if self.current_state == "GENERATE PACKET" and signal == Hardware.EVENTS.ClassA.GENERATE_PACKET:
            self.current_state = "TRANSMIT"

        if self.current_state == "TRANSMIT":
            if signal == Hardware.EVENTS.ClassA.TRANSMISSION_START:
                pass
            elif signal == Hardware.EVENTS.ClassA.TRANSMISSION_END:
                self.current_state = "DELAY_RX1"

        if self.current_state == "DELAY_RX1":
            if signal == Hardware.EVENTS.ClassA.DELAY_START:
                pass
            elif signal == Hardware.EVENTS.ClassA.DELAY_END:
                self.current_state = "RX1"






