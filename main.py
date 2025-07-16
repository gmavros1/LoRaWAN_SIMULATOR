# from LoRaModule import LoRaModule
# from WakeUpRadioModule import WakeUpRadioModule

LORA_NODE_PARAMETERS = "./LoRaNodeParameters.json"
WAKE_UP_RADIO_PARAMETERS = "./MangalKingetWuR.json"

from signals import Location
from Environment import Environment
from SensorNode import SensorNode

environment =  Environment()

node1_location = Location(0, 0)
node2_location = Location(0, 50)
node3_location = Location(0, 1000)

sensor_1 = SensorNode("1", WAKE_UP_RADIO_PARAMETERS, LORA_NODE_PARAMETERS, node1_location)
sensor_2 = SensorNode("2", WAKE_UP_RADIO_PARAMETERS, LORA_NODE_PARAMETERS, node2_location)
sensor_3 = SensorNode("3", WAKE_UP_RADIO_PARAMETERS, LORA_NODE_PARAMETERS, node3_location)

payload = {"messages": "DUMMY PAYLOAD", "METRIC1": "TEMPERATURE=12C", "METRIC2": "HUMIDITY=34"}
header = {"destination": "00000"}
#
# sensor_1.lora.generate_packet(0, payload, header)
# wireless_packet = sensor_1.lora.transmit_packet()
# environment.add_packet(wireless_packet)
#
# sensor_2.wurx.generate_beacon(0)
# wur_beacon = sensor_2.wurx.transmit_beacon()
# environment.add_wake_up_beacon(wur_beacon)

print(environment)

simulation_time = 111
for time_slot in range(simulation_time):
    # sensor_3.lora.receive_packets_partial(environment)
    # sensor_1.wurx.listen(environment)
    environment.tick()
    print(environment)

# print(node2.RX_Buffer)
