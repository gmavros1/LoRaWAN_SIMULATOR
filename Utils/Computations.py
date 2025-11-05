import math
import hashlib

def compute_payload_size(payload: dict) -> int:
    payload_size: int = 0
    for value in payload.values():
        payload_size += len(str(value).encode('utf-8'))

    return payload_size

def toa(payload_size: int, sf: int, bw: int = 125, crc: int =1, header: int =0, de: int =0, n_preamble: int =8, cr: int =1) -> int:
    # The LowDataRateOptimize is enabled fo bandwidth 125 kHz and Spreading Factor >= 11
    if bw == 125 and int(sf) >= 11: de = 1

    # Time of symbol (ms)
    time_of_symbol = (2 ** int(sf)) / bw

    # Time of payload - include header crc and low data range optimization
    num_payload_symbols = 8 + max(math.ceil((8.0 * payload_size - 4.0 * int(sf) + 28.0 + 16.0 * crc - 20.0 * header) / (4.0 * (int(sf) - 2.0 * de))) * (cr + 4), 0)
    time_of_payload = time_of_symbol * num_payload_symbols
    time_of_preamble = preamble_time(sf, bw, n_preamble)

    return time_of_preamble + time_of_payload

def preamble_time(sf: int, bw: int = 125, n_preamble: int =8) -> int:
    # Time of symbol (ms)
    time_of_symbol = (2 ** int(sf)) / bw
    time_of_preamble = (n_preamble + 4.25) * time_of_symbol

    return time_of_preamble


def calculate_received_power(distance:float, transmission_power: int, shadowing_std_dev: float=6.0):
    # Constants - sensors-22-03518-v3.pdf - reference
    PLd0 = 37  # Reference path loss at the reference distance (d0)
    d0 = 1.0  # Reference distance (1 meter)
    alpha = 2.5  # Path loss exponent - (2-4) - urban enviroments ~ 3
    # Calculate the path loss without shadowing
    try:
        PL = PLd0 + 10 * alpha * math.log10(distance / d0)
    except:
        print(distance)
    # Generate a random value for shadowing
    shadowing = shadowing_std_dev
    # Calculate the total path loss with shadowing
    PL += shadowing
    # Receive power returned in dB
    Pr = transmission_power - PL

    return Pr


def distance(location1, location2) -> float:
    x1, y1, z1 = location1.x, location1.y, 0
    x2, y2, z2 = location2.x, location2.y, 0

    distance = math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2 + (z2 - z1) ** 2)
    return distance

# Use this function to sort nodes.
# nodes where its action is transmit goes first.
def sync_transmit_receive(devices):
    tx_list, other = [], []

    TX_FUNC     = devices[0].lora.__class__.transmit_packet
    TX_WUR_FUNC = devices[0].wurx.__class__.transmit_beacon

    for dev in devices:                      # single pass
        exec_ = getattr(dev.action, "executable", None)
        func  = getattr(exec_, "__func__", None)  # underlying function
        if func in (TX_FUNC, TX_WUR_FUNC):
            tx_list.append(dev)
        else:
            other.append(dev)

    return tx_list + other                   # new ordering

# Get unique delays for nodes for join request transmission
def spaced_delay_from_id(node_id: str, step=1000) -> int:
    # Hash the string ID into a large integer
    h = int(hashlib.sha256(node_id.encode()).hexdigest(), 16)
    # Use the hash to select a slot
    slot = h % 100  # supports up to 1000 nodes
    return slot * step

# a in path loss model -> 2.5, shadowing -> 6.0
# print(calculate_received_power(5500, 14)) # SF7 5500 km
# print(calculate_received_power(7400, 14)) # SF8 7400 km
# print(calculate_received_power(9800, 14)) # SF9 9800 km
# print(calculate_received_power(12500, 14)) # SF10 12500 km
# print(calculate_received_power(16000, 14)) # SF11 16000 km
# print(calculate_received_power(20000, 14)) # SF12 20000 km
# print(calculate_received_power(1500, 14)) # -109 dbm 1500 m
# payload = {"control": "JOIN_ACCEPT", "SF": 12}
# header = {"destination": "00000"}
# print(compute_payload_size(payload))
