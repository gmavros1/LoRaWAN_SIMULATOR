import Metrics.Statistics
import Utils.Computations
from Wireless.signals import Location
from Physics.Environment import Environment
from Devices.LoRaWANClassANode import LoRaWANNode
from Devices.LoRaWANGateway import LoRaWANGateway
from Devices.NetworkServer import  NetworkServer
from tqdm import tqdm
import numpy as np
import json

class Simulation:

    def __init__(
            self,
            simulation_time,
            generation_prob,
            lora_config: str = "Configurations/LoRaNodeParameters.json",
            wur_config: str = "Configurations/DUMPWuR_testing.json",
            devices_config: str = "Topology/topology.json",
            device_type = LoRaWANNode,
            gateway_type = LoRaWANGateway
            ):

        self.LORA_NODE_PARAMETERS = lora_config
        self.WAKE_UP_RADIO_PARAMETERS = wur_config
        self.DEVICES_PARAMETERS = devices_config
        self.environment = Environment()
        self.device_type = device_type
        self.gateway_type = gateway_type
        self.Devices = []
        self.simulation_time = simulation_time
        self.event_prob_generation = generation_prob
        self.NetworkServer = NetworkServer()

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
            node.lora.SF = node_config["default_sf"]
            node.lora.Channel = node_config["default_channel"]
            node.lora.RSSI = node.lora.RSSIs[str(node.lora.SF)]
            node.event_generator.probability = self.event_prob_generation
            self.Devices.append(node)

        # GATEWAYS
        end_devices_config = data["Gateways"]
        for node_config in end_devices_config:
            node = self.gateway_type(node_config["ID"],
                                    self.WAKE_UP_RADIO_PARAMETERS,
                                    self.LORA_NODE_PARAMETERS,
                                    Location(node_config["Location"]["x"], node_config["Location"]["y"]), self.environment, self.NetworkServer)
            self.Devices.append(node)


    def run(self):
        print("SIMULATION \n")

        for i in tqdm(range(self.simulation_time), desc="Simulating") :

            for device in Utils.Computations.sync_transmit_receive(self.Devices):
                interrupt, wireless_signal = device.action.executable(*device.action.args)
                self.environment.add_packet(wireless_signal)
                self.environment.add_wake_up_beacon(wireless_signal)
                device.protocol_driver(interrupt, i, self.environment)

            # print(self.environment)
            self.environment.tick()

    def check_if_all_nodes_have_joined(self):
        end_devices = [item for item in self.Devices if not isinstance(item, LoRaWANGateway)]

        for d in end_devices:
            if not d.joined_to_network:
                return False

        return True

    def initialize_network(self):
        print("JOIN PROCESS \n")

        for device in self.Devices:
            print(str(device.lora.ID) + " " +  str(device.lora.SF))

        i = 0
        while True :
            for device in Utils.Computations.sync_transmit_receive(self.Devices):
                interrupt, wireless_signal = device.action.executable(*device.action.args)
                self.environment.add_packet(wireless_signal)
                self.environment.add_wake_up_beacon(wireless_signal)
                device.join_driver(interrupt, i, self.environment)

            i += 1
            if self.check_if_all_nodes_have_joined():
                break

            # print(self.environment)
            self.environment.tick()

        for device in self.Devices:
            print(str(device.lora.ID) + " " +  str(device.lora.SF) + " " + str(device.joined_to_network))

    def end_of_simulation(self):

        generated_packets = 0
        successfully_received_packets_list = []
        for devices in self.Devices:
            generated_packets += devices.lora.generated_packets
            successfully_received_packets_list += devices.lora.successfully_received_packets

        successfully_received_packets = len(list(dict.fromkeys(successfully_received_packets_list)))

        return generated_packets, successfully_received_packets
