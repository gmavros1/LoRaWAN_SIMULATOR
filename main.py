# from LoRaModule import LoRaModule
# from WakeUpRadioModule import WakeUpRadioModule

LORA_NODE_PARAMETERS = "Configurations/LoRaNodeParameters.json"
WAKE_UP_RADIO_PARAMETERS = "Configurations/MangalKingetWuR.json"

from Wireless.signals import Location
from Physics.Environment import Environment
from Hardware.SensorNode import SensorNode

environment =  Environment()

node1_location = Location(0, 1000)
node2_location = Location(0, 50)
node3_location = Location(0, 0)

sensor_1 = SensorNode("1", WAKE_UP_RADIO_PARAMETERS, LORA_NODE_PARAMETERS, node1_location)
sensor_2 = SensorNode("2", WAKE_UP_RADIO_PARAMETERS, LORA_NODE_PARAMETERS, node2_location)
sensor_3 = SensorNode("3", WAKE_UP_RADIO_PARAMETERS, LORA_NODE_PARAMETERS, node3_location)

payload = {"messages": "DUMMY PAYLOAD"}
header = {"destination": "00000"}

sensor_1.lora.generate_packet(0, payload, header)
# sensor_2.lora.generate_packet(0, payload, header)

# wireless_packet = sensor_1.lora.transmit_packet()

sensor_2.wurx.generate_beacon(0)
# wur_beacon = sensor_2.wurx.transmit_beacon()
# environment.add_wake_up_beacon(wur_beacon)

print(environment)

simulation_time = 111
for time_slot in range(simulation_time):

    wireless_packet1 = sensor_1.lora.transmit_packet()
    # wireless_packet2 = sensor_2.lora.transmit_packet()
    wur_beacon = sensor_2.wurx.transmit_beacon()

    environment.add_packet(wireless_packet1)
    # environment.add_packet(wireless_packet2)
    environment.add_wake_up_beacon(wur_beacon)

    sensor_3.lora.receive_packets_partial(environment)
    sensor_3.wurx.listen(environment)
    # sensor_1.wurx.listen(environment)
    print(environment)
    environment.tick()


# print(node2.RX_Buffer)
