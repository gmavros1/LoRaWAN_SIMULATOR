from Wireless.signals import Location                 # your neutral datatypes module
from Hardware.WakeUpRadioModule import WakeUpRadioModule
from Hardware.LoRaModule import LoRaModule

class Action:
    executable = None
    args = []

class SensorNode:
    """
    Real-world sensor that sleeps until its wake-up receiver triggers,
    then forwards a LoRa packet.  Composition avoids circular imports.
    """
    def __init__(self, node_id: str, wurx_json: str, lora_json: str, position: Location):
        self.ID = node_id
        self.location = position

        # two internal radios -------------------------------------------
        self.wurx = WakeUpRadioModule(f"{node_id}-WuRx", wurx_json, position)
        self.lora = LoRaModule       (f"{node_id}-LoRa", lora_json, position)

        # application-layer state
        self.seq_no: int = 0

        # Function que. The next action of sensor is defined
        self.action = Action()

        # CLASS A PROTOCOL, PRESENTED IN ALL CLASSES
        self.receiving_windows_enabled: bool = False
        self.RECEIVE_DELAY_1: int = 5000
        self.RECEIVE_DELAY_2: int = 1000
        self.joined_to_network: bool = False # Default value

        # The network where the device has joined
        self.joined_network_id = None
