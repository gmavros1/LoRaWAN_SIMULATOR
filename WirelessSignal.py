from LoRaPacket import LoRaPacket

class WirelessSignal:
    def __init__(self, lora_packet: LoRaPacket, node):
        self.lora_packet = lora_packet
        self.channel = node.Channel
        self.sf = node.SF
        self.bandwidth = node.Bandwidth
        self.tx_power = node.PowerTX
        self.source_location = node.location

        # Helpers during capture
        self.rx_power = None
        self.time_over_air_required =  None # How many ms is on air
