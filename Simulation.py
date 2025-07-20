import Utils.Computations
from Wireless.signals import Location
from Physics.Environment import Environment
from Devices.LoRaWANClassANode import LoRaWANNode
from Devices.LoRaWANGateway import LoRaWANGateway
import json

class Simulation:

    def __init__(
            self,
            lora_config: str = "Configurations/LoRaNodeParameters.json",
            wur_config: str = "Configurations/MangalKingetWuR.json",
            devices_config: str = "Configurations/DefaultDevicesLocation.json",
            device_type = LoRaWANNode):

        self.LORA_NODE_PARAMETERS = lora_config
        self.WAKE_UP_RADIO_PARAMETERS = wur_config
        self.DEVICES_PARAMETERS = devices_config
        self.environment = Environment()
        self.device_type = device_type
        self.Devices = []
        self.set_up_devices()

    def set_up_devices(self):
        with open(self.DEVICES_PARAMETERS, "r", encoding="utf-8") as f:
            data = json.load(f)

        # END DEVICES
        end_devices_config = data["Nodes"]
        for node_config in end_devices_config:
            node = self.device_type(node_config["ID"],
                                    self.WAKE_UP_RADIO_PARAMETERS,
                                    self.LORA_NODE_PARAMETERS,
                                    Location(node_config["Location"]["x"], node_config["Location"]["y"]))
            self.Devices.append(node)

        # END DEVICES
        end_devices_config = data["Gateways"]
        for node_config in end_devices_config:
            node = LoRaWANGateway(node_config["ID"],
                                    self.WAKE_UP_RADIO_PARAMETERS,
                                    self.LORA_NODE_PARAMETERS,
                                    Location(node_config["Location"]["x"], node_config["Location"]["y"]), self.environment)
            self.Devices.append(node)


    def run(self):
        for i in range(1000):

            for device in Utils.Computations.sync_transmit_receive(self.Devices):
                interrupt, wireless_signal = device.action.executable(*device.action.args)
                self.environment.add_packet(wireless_signal)
                self.environment.add_wake_up_beacon(wireless_signal)
                device.protocol_driver(interrupt, i, self.environment, wireless_signal)

            print(self.environment)
            self.environment.tick()


sim = Simulation()
sim.run()