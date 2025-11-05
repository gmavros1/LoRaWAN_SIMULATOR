from Devices.LoRaWANGateway import LoRaWANGateway
import Hardware.EVENTS
import Wireless.signals

class MultihopGateway(LoRaWANGateway):

    def __init__(self, node_id: str, wurx_json: str, lora_json: str, position: Wireless.signals.Location, environment, NetworkServer):
        super().__init__(node_id, wurx_json, lora_json, position, environment, NetworkServer)

    def generate_accept_packet(self, time):
        received_join_request = self.lora.TX_Buffer.pop()
        payload = {"control": "JOIN_ACCEPT", "SF": self.suggest_sf(received_join_request.received_power)}
        header = {"destination": "00000"}

        self.lora.generate_packet(time, payload, header)
        self.lora.TX_Buffer[-1].Destination = received_join_request.Source
        return Hardware.EVENTS.ClassA.GENERATE_PACKET, None