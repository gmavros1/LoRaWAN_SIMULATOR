from Metrics import Statistics
from Simulation import Simulation
# from Topology.Simple_topology_1 import TopologyGenerator
from Topology.Multihop_topology import MultihopTopologyGenerator
from Devices.LoRaWANClassANode import LoRaWANNode
from Devices.LoRaWANGateway import LoRaWANGateway
from Devices.Multihop1Node import Multihop1Node
from Devices.MultihopGateway import MultihopGateway
from Topology.plot import gateways

# ============================================================================
# SIMULATION PARAMETERS
# ============================================================================
NUMBER_OF_NODES = 10
MAX_NODE_DISTANCE_M = 600
MAX_RADIUS_M = 12000
DEFAULT_SF = 12
DEFAULT_CHANNEL = 1
SIMULATION_TIME = 500000
SLOT_MS = 31

# ============================================================================
# PROTOCOL SELECTION
# ============================================================================
# Available protocols:
#   - LoRaWANNode: Standard LoRaWAN Class A with RX1/RX2 windows
#   - Multihop1Node: Multihop clustering protocol with relay capability
# ============================================================================

# Select protocols to test (can test multiple protocols in one run)
PROTOCOLS_TO_TEST = [
    # {"name": "LoRaWAN Class A", "device_type": LoRaWANNode, "gateway_type": LoRaWANGateway},
    {"name": "Multihop Protocol", "device_type": Multihop1Node, "gateway_type": MultihopGateway}
]

# Traffic load probabilities to test
TRAFFIC_LOADS = [1, 1.5, 2, 2.5, 3, 3.5, 4, 4.5, 5, 5.5, 6, 6.5, 7, 10]

# ============================================================================
# RUN EXPERIMENTS
# ============================================================================

# Generate topology once (same topology for all protocols)
# topology_generator = TopologyGenerator(NUMBER_OF_NODES, MAX_NODE_DISTANCE_M, MAX_RADIUS_M, DEFAULT_SF, DEFAULT_CHANNEL)
# topology_generator = MultihopTopologyGenerator()
# topology_generator.generate() # Writes the topology in topology.json

# Run experiments for each protocol
for protocol_config in PROTOCOLS_TO_TEST:
    protocol_name = protocol_config["name"]
    device_type = protocol_config["device_type"]
    gateway_type = protocol_config["gateway_type"]

    print(f"\n{'='*70}")
    print(f"Testing Protocol: {protocol_name}")
    print(f"{'='*70}\n")

    statistics = Statistics.AlohaValidation()

    for i in TRAFFIC_LOADS:
        gen_probability = 1 / (i * SLOT_MS * NUMBER_OF_NODES)

        # Create simulation with selected device type
        sim = Simulation(SIMULATION_TIME, gen_probability, device_type=device_type, gateway_type=gateway_type)
        sim.initialize_network()
        sim.run()

        generated_packets, successfully_received = sim.end_of_simulation()
        print(f"Load factor {i}: Generated={generated_packets}, Received={successfully_received}")

        statistics.add_run(gen_probability, generated_packets, successfully_received,
                          sim_duration_ms=SIMULATION_TIME, slot_ms=SLOT_MS, n_nodes=NUMBER_OF_NODES)

    # Plot results for this protocol
    statistics.plot(f"{protocol_name} - Performance")
