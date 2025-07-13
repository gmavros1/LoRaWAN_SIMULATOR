from os import environ

from LoRaModule import LoRaModule, Location
from Environment import Environment

environment =   Environment()

node1_location = Location(0, 800)
node2_location = Location(0, 1200)
node3_location = Location(0, 0)


node1 = LoRaModule("1", "./LoRaNodeParameters.json", node1_location)
node2 = LoRaModule("2", "./LoRaNodeParameters.json", node2_location)
node3 = LoRaModule("3", "./LoRaNodeParameters.json", node3_location)

# Transmission
payload = {"messages": "23f", "levelsource": "3"}
header = {"destination": "00000"}

node1.generate_packet(generation_time=1000, payload= payload, header={"destination": "3"})
wireless_packet = node1.transmit_packet()
environment.add_packet(wireless_packet)

node2.generate_packet(generation_time=1000, payload= payload, header={"destination": "3"})
wireless_packet = node2.transmit_packet()
environment.add_packet(wireless_packet)


print(environment)

simulation_time = 35
for time_slot in range(simulation_time):
    node3.receive_packets_partial(environment)
    environment.tick()
    print(environment)

print(node2.RX_Buffer)
