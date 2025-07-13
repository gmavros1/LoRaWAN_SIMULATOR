from os import environ

from LoRaModule import LoRaModule, Location
from pprint import pprint
from Environment import Environment

node_location = Location(3, 6)
node = LoRaModule("0", "./LoRaNodeParameters.json", node_location)
payload = {"messages": "23f", "levelsource": "3"}
header = {"destination": "00000"}
node.generate_packet(generation_time=1000, payload= payload, header=header)
wireless_packet = node.transmit_packet()

environment =   Environment()
environment.add_packet(wireless_packet)

for time_slot in range(100):
    environment.tick()
    print(environment)
