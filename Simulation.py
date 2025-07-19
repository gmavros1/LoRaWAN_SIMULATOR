from Wireless.signals import Location
from Physics.Environment import Environment
from Devices.LoRaWANClassANode import LoRaWANNode
from Devices.LoRaWANGateway import LoRaWANGateway

LORA_NODE_PARAMETERS = "Configurations/LoRaNodeParameters.json"
WAKE_UP_RADIO_PARAMETERS = "Configurations/MangalKingetWuR.json"

environment = Environment()

node1_location = Location(0, 1000)
node1 = LoRaWANNode("1", WAKE_UP_RADIO_PARAMETERS, LORA_NODE_PARAMETERS, node1_location)
gateway_location = Location(0, 0)
gateway = LoRaWANGateway("0", WAKE_UP_RADIO_PARAMETERS, LORA_NODE_PARAMETERS, gateway_location, environment)

Devices = [node1, gateway]

# @TODO:
# Use callback to sort nodes.
# nodes where its action is transmit goes first.

def run():
    for i in range(100000):

        for device in Devices:
            interrupt, wireless_signal = device.action.executable(*device.action.args)
            environment.add_packet(wireless_signal)
            environment.add_wake_up_beacon(wireless_signal)
            device.protocol_driver(interrupt, i, environment, wireless_signal)

        # print(environment)
        environment.tick()

run()