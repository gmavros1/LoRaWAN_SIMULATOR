from Wireless.LoRaPacket import LoRaPacket

class WakeUpBeacon:                       # tiny “packet”
    def __init__(self, gen_time: int, src_id: str):
        self.ID = f"{src_id}-{gen_time}"

# signals.py
class Location:
    def __init__(self, x: float = 0, y: float = 0): self.x, self.y = x, y

class LoRaWirelessSignal:
    def __init__(self, lora_packet: LoRaPacket , node):
        self.lora_packet = lora_packet
        self.channel = node.Channel
        self.sf = node.SF
        self.bandwidth = node.Bandwidth
        self.tx_power = node.PowerTX
        self.source_location = node.location

        # Helpers during capture
        self.rx_power = None
        self.time_over_air_required =  None # How many ms is on air


class OOKRZWirelessSignal:
    def __init__(self, beacon: WakeUpBeacon, source_module, time_over_air: int):
        self.beacon          = beacon
        self.channel_MHz     = source_module.CenterFreq_MHz
        self.tx_power_dBm    = source_module.PowerTX_dBm
        self.source_location = source_module.location
        # arrival power filled in by propagation model later
        self.rx_power_dBm    = None
        self.time_over_air_required =  time_over_air # How many ms is on air
