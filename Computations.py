import math


def compute_payload_size(payload: dict) -> int:
    payload_size: int = 0
    for value in payload.values():
        payload_size += len(value.encode('utf-8'))

    return payload_size

def toa(payload_size: int, sf: int, bw: int = 125, crc: int =1, header: int =0, de: int =0, n_preamble: int =8, cr: int =1) -> int:
    # The LowDataRateOptimize is enabled fo bandwidth 125 kHz and Spreading Factor >= 11
    if bw == 125 and int(sf) >= 11: de = 1

    # Time of symbol (ms)
    time_of_symbol = (2 ** int(sf)) / bw

    # Time of payload - include header crc and low data range optimization
    num_payload_symbols = 8 + max(math.ceil((8.0 * payload_size - 4.0 * int(sf) + 28.0 + 16.0 * crc - 20.0 * header) / (4.0 * (int(sf) - 2.0 * de))) * (cr + 4), 0)
    time_of_payload = time_of_symbol * num_payload_symbols
    time_of_preamble = (n_preamble + 4.25) * time_of_symbol

    return time_of_preamble + time_of_payload
