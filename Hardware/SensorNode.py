from Wireless.signals import Location                 # your neutral datatypes module
from Hardware.WakeUpRadioModule import WakeUpRadioModule
from Hardware.LoRaModule import LoRaModule

class SensorNode:
    """
    Real-world sensor that sleeps until its wake-up receiver triggers,
    then forwards a LoRa packet.  Composition avoids circular imports.
    """
    def __init__(
        self,
        node_id: str,
        wurx_json: str,
        lora_json: str,
        position: Location,
    ):
        self.ID = node_id
        self.location = position

        # two internal radios -------------------------------------------
        self.wurx = WakeUpRadioModule(f"{node_id}-WuRx", wurx_json, position)
        self.lora = LoRaModule       (f"{node_id}-LoRa", lora_json, position)

        # application-layer state
        self.seq_no: int = 0
