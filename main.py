from Metrics import Statistics
from Simulation import Simulation
from Topology.Simple_topology_1 import TopologyGenerator

NUMBER_OF_NODES = 10
MIN_NODE_DISTANCE_M = 200
MAX_RADIUS_M = 12000
DEFAULT_SF = 12
DEFAULT_CHANNEL = 1
SIMULATION_TIME = 500000
SLOT_MS = 31

statistics = Statistics.AlohaValidation()
topology_generator = TopologyGenerator(NUMBER_OF_NODES, MIN_NODE_DISTANCE_M, MAX_RADIUS_M, DEFAULT_SF, DEFAULT_CHANNEL)
topology_generator.generate()

probs = [1, 1.5, 2, 2.5, 3, 3.5, 4, 4.5, 5, 5.5, 6, 6,5, 7, 10]
for i in probs:
    gen_probability = 1 / (i * SLOT_MS * NUMBER_OF_NODES)
    sim = Simulation(SIMULATION_TIME, gen_probability)
    sim.initialize_network()
    sim.run()
    print(sim.end_of_simulation())
    generated_packets, successfully_received = sim.end_of_simulation()
    statistics.add_run(gen_probability,generated_packets, successfully_received, sim_duration_ms=SIMULATION_TIME, slot_ms=SLOT_MS, n_nodes=NUMBER_OF_NODES)

statistics.plot("SIMULATION 1")
