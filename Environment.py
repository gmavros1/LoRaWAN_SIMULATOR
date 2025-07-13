from WirelessSignal import WirelessSignal
import numpy as np
from typing import List
import Computations

N_CHANNELS = 9
N_SF       = 6          # SF7–SF12

class _PacketRecord:

    def __init__(self, signal: WirelessSignal, toa_left: int) -> None:
        self.signal    = signal          # the original WirelessSignal instance
        self.toa_left  = int(toa_left)   # time-over-air still to elapse (ticks)

    def tick(self) -> bool:
        """Decrease timer by one; return True if the packet is still alive."""
        self.toa_left -= 1
        return self.toa_left >= 0

class Environment:
        """
        Stores in-flight LoRa packets in a 2-D bucket:
          packet_over_air[channel][sf] -> List[_PacketRecord]

        Channel index 0-8 corresponds to the nine EU868 125-kHz channels
        SF index 0-5   corresponds to SF7 … SF12.
        """
        N_CHANNELS = 9
        N_SF = 6  # SF7–SF12

        def __init__(self) -> None:
            # channel first, SF second (so env[chan][sf])
            self.packet_over_air: List[List[List[_PacketRecord]]] = [
                [[] for _ in range(self.N_SF)] for _ in range(self.N_CHANNELS)
            ]

        # ------------------------------------------------------------------
        # Public API
        # ------------------------------------------------------------------
        def add_packet(self, signal: WirelessSignal) -> None:
            """Insert a new packet with its initial airtime budget (in ticks)."""
            time_over_air_required: int = Computations.toa(
                Computations.compute_payload_size(signal.lora_packet.Payload), signal.sf)
            self._check_indices(signal.channel - 1, signal.sf - 7)
            signal.time_over_air_required = time_over_air_required
            self.packet_over_air[signal.channel - 1][signal.sf - 7].append(_PacketRecord(signal, time_over_air_required))

        def tick(self) -> None:
            """
            Advance the simulation by one tick:
            – decrement airtime for every packet
            – drop records whose timer reached zero.
            """
            for ch_buckets in self.packet_over_air:
                for bucket in ch_buckets:
                    # iterate in place while safely removing dead packets
                    i = 0
                    while i < len(bucket):
                        if bucket[i].tick():
                            i += 1  # packet still active
                        else:
                            bucket.pop(i)  # drop expired packet

        # ------------------------------------------------------------------
        # Helpers
        # ------------------------------------------------------------------
        def _check_indices(self, channel: int, sf: int) -> None:
            if not (0 <= channel < self.N_CHANNELS and 0 <= sf < self.N_SF):
                raise IndexError("channel or SF index out of range")

        def snapshot_remaining_toa(self) -> list:
            """Nested plain-Python list; always works."""
            return [
                [[p.toa_left for p in bucket] for bucket in ch_buckets]
                for ch_buckets in self.packet_over_air
            ]

        def __str__(self) -> str:
            return str(self.snapshot_remaining_toa())




