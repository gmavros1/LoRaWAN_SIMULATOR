# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a discrete-event LoRaWAN network simulator written in Python. It simulates LoRa wireless communication between end devices (nodes), gateways, and a network server, modeling the physical layer, MAC layer protocols (Class A), and network topology.

## Running Simulations

**Run the main simulation:**
```bash
python main.py
```

The simulator uses millisecond-granularity ticks and processes devices in transmit-then-receive order for proper collision handling.

## Core Architecture

### Simulation Flow

1. **Initialization** (`Simulation.__init__`): Loads device configurations from JSON files and instantiates nodes and gateways
2. **Network Join** (`Simulation.initialize_network`): OTAA (Over-The-Air Activation) join process where nodes send JOIN_REQUEST and gateways respond with JOIN_ACCEPT containing suggested spreading factors
3. **Main Loop** (`Simulation.run`): Discrete-event loop that:
   - Processes device actions in transmit-first order (via `Utils.Computations.sync_transmit_receive`)
   - Adds wireless signals to the environment
   - Advances environment by one tick
   - Repeats for configured simulation time

### Key Components

**Simulation** (`Simulation.py`): Main orchestrator
- Manages the discrete-event simulation loop
- Coordinates device initialization and network join process
- Collects statistics at end of simulation

**Environment** (`Physics/Environment.py`): The wireless medium
- Stores in-flight LoRa packets in 2D buckets: `lora_packet_over_air[channel][sf]`
- Channel indices 0-8 map to EU868 125kHz channels
- SF indices 0-5 map to SF7-SF12
- Each bucket contains `_PacketRecord` objects tracking remaining time-over-air
- `tick()` method advances time and removes expired packets

**Devices** (`Devices/`):
- `SensorNode`: Base class with LoRa and WakeUpRadio modules, uses action-based state machine
- `LoRaWANClassANode`: Implements LoRaWAN Class A protocol with RX1/RX2 receive windows
- `LoRaWANGateway`: Listens on multiple SF/channel combinations simultaneously (up to 8 parallel)
- `Multihop1Node`: Extends Class A with multihop clustering and relay capabilities
- `NetworkServer`: Placeholder for network-level logic (currently minimal)

**Hardware Modules** (`Hardware/`):
- `LoRaModule`: Handles packet generation, transmission, reception with capture effect (6 dB margin), and segmentation
- `WakeUpRadioModule`: Low-power wake-up receiver
- `EVENTS`: Defines the interrupt/event types for protocol state machines

**Protocol Drivers**: Each device has two state machine drivers:
- `join_driver()`: Handles OTAA join process with JOIN_REQUEST/JOIN_ACCEPT exchanges
- `protocol_driver()`: Normal operation after joining (packet generation, transmission, receive windows)

State machines work via `action.executable` function pointers and respond to `Hardware.EVENTS.ClassA` interrupts.

**LoRaWAN Class A Protocol**:
- Node transmits uplink when event occurs
- Node opens RX1 window after RECEIVE_DELAY_1 (5000ms)
- If no downlink, opens RX2 window after RECEIVE_DELAY_2 (1000ms)
- Gateways can send downlink in either window
- Contention window with random backoff for join retries

### Wireless Signal Handling

**Packet Structure** (`Wireless/LoRaPacket.py`):
- Packets have unique IDs: `Source + Destination + GenerationTime`
- Support segmentation via `segment_counter` for long airtime transmissions
- Track metadata: SF, channel, received power

**Signal Processing** (`Hardware/LoRaModule.py`):
- `receive_packets_partial()`: Called each tick during reception
  - Filters packets by RSSI threshold
  - Implements capture effect: if strongest signal is 6 dB stronger than second, it's received
  - Accumulates packet segments in `RX_Buffer`
- `decode_packet()`: Groups segments by packet ID and validates complete reception

### Topology and Configuration

**Topology** (`Topology/Simple_topology_1.py`):
- `TopologyGenerator.generate()` creates network layout
- Outputs to `Topology/topology.json` with node/gateway positions and default SF/channel

**Configuration Files** (`Configurations/`):
- `LoRaNodeParameters.json`: LoRa radio settings (SF, channel, bandwidth, TX power, RSSI thresholds per SF)
- `MangalKingetWuR.json`: Wake-up radio parameters
- Device locations stored in topology JSON

### Physical Layer

**Path Loss Model** (`Utils/Computations.py`):
- Log-distance path loss: `PL = PLd0 + 10 * alpha * log10(distance / d0) + shadowing`
- Default: PLd0=37 dB, alpha=2.5 (urban), shadowing=6 dB
- `calculate_received_power()`: Returns received power in dBm

**Time-over-Air** (`Utils/Computations.py`):
- `toa()`: Calculates LoRa packet airtime in milliseconds
- Enables Low Data Rate Optimization for BW=125kHz and SF>=11
- Accounts for preamble, header, CRC, coding rate

### Statistics and Metrics

**Metrics** (`Metrics/Statistics.py`):
- `AlohaValidation` class tracks generated vs successfully received packets
- Plots throughput curves for different traffic loads

## Code Patterns

**Device Action State Machine**:
```python
# Each device has an Action with executable function and args
self.action.executable, self.action.args = some_function, [arg1, arg2]

# In simulation loop:
interrupt, signal = device.action.executable(*device.action.args)
device.protocol_driver(interrupt, time, environment)
```

**Interrupt-Driven Protocol**:
- Functions return `(interrupt_event, signal)` tuples
- Protocol driver switches to next state based on interrupt type
- Example: `TRANSMISSION_END` → `receive_delay_1` → `RX1_DELAY_END` → `rx_1` → `PACKET_DECODED` → `sleep`

**Transmit-Receive Ordering**:
- `Utils.Computations.sync_transmit_receive()` sorts devices so transmitters go first
- Ensures packets are in environment before receivers check

## Important Implementation Details

- **Segmented Transmission**: Packets may span multiple ticks. `LoRaModule.transmit_packet()` creates segments and re-enqueues remaining segments.
- **Partial Reception**: `receive_packets_partial()` is called every tick during RX windows to handle streaming reception.
- **Join Process SF Assignment**: Gateways suggest optimal SF based on received signal strength in JOIN_ACCEPT payload.
- **Channel Sensing**: Multihop nodes implement carrier sensing before transmission to avoid collisions.
- **Capture Effect**: Can be toggled in `LoRaModule.receive_packets_partial()` (currently enabled with 6 dB threshold).

## Key Dependencies

- `tqdm`: Progress bars for simulation
- `numpy`: Numerical operations (minimal usage)
- `json`: Configuration loading
- `matplotlib`: Plotting (in Metrics)

## Extending the Simulator

**Adding New Node Types**:
1. Inherit from `SensorNode` or `LoRaWANClassANode`
2. Implement custom `protocol_driver()` and/or `join_driver()`
3. Define state transitions based on `Hardware.EVENTS.ClassA` interrupts
4. Update `Simulation.set_up_devices()` to support new device type

**Adding New Protocols**:
- Define new event types in `Hardware/EVENTS.py`
- Implement new receive window timing or transmission patterns
- Modify gateway behavior if downlink patterns change

**Custom Traffic Models**:
- Extend `Utils.TrafficModel.TrafficModel` class
- Assign to node's `event_generator` field
