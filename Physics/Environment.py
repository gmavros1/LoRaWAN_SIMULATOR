import Utils.Computations
from Wireless.signals import LoRaWirelessSignal, OOKRZWirelessSignal
from typing import List

N_CHANNELS = 9
N_SF       = 6          # SF7–SF12

class _PacketRecord:

    def __init__(self, signal: LoRaWirelessSignal | OOKRZWirelessSignal, toa_left: int) -> None:
        self.signal    = signal          # the original WirelessSignal instance
        self.toa_left  = int(toa_left)   # time-over-air still to elapse (ticks)

    def tick(self) -> bool:
        """Decrease timer by one; return True if the packet is still alive."""
        self.toa_left -= 1
        return self.toa_left >= 0

class Environment:
        """
        Stores in-flight LoRa packets in a 2-D bucket:
          lora_packet_over_air[channel][sf] -> List[_PacketRecord]

        Channel index 0-8 corresponds to the nine EU868 125-kHz channels
        SF index 0-5   corresponds to SF7 … SF12.
        """
        N_CHANNELS = 9
        N_SF = 6  # SF7–SF12

        def __init__(self) -> None:
            # channel first, SF second (so env[chan][sf])
            self.lora_packet_over_air: List[List[List[_PacketRecord]]] = [
                [[] for _ in range(self.N_SF)] for _ in range(self.N_CHANNELS)
            ]

            self.wur_packets_over_air: List[_PacketRecord] = []

        # ------------------------------------------------------------------
        # Public API
        # ------------------------------------------------------------------
        def add_packet(self, signal: LoRaWirelessSignal) -> None:
            """Insert a new packet with its initial airtime budget (in ticks)."""
            if signal is None:
                return
            self._check_indices(signal.channel - 1, signal.sf - 7) # check channel and sf
            signal.time_over_air_required = Utils.Computations.toa(Utils.Computations.compute_payload_size(signal.lora_packet.Payload),signal.sf)
            self.lora_packet_over_air[signal.channel - 1][signal.sf - 7].append(_PacketRecord(signal, signal.lora_packet.segment_counter))

        def add_wake_up_beacon(self, signal: OOKRZWirelessSignal) -> None:
            self.wur_packets_over_air.append(_PacketRecord(signal, signal.time_over_air_required))

        def tick(self) -> None:
            """
            Advance the simulation by one tick:
            – decrement airtime for every packet
            – drop records whose timer reached zero.
            """
            for ch_buckets in self.lora_packet_over_air:
                for bucket in ch_buckets:
                    # iterate in place while safely removing dead packets
                    i = 0
                    while i < len(bucket):
                        bucket.pop(i)  # drop expired fragment of packet

            """
            Handle wur radio signal same way
            """
            i = 0
            while i < len(self.wur_packets_over_air):
                if self.wur_packets_over_air[i].tick():
                    i += 1  # packet still active
                else:
                    self.wur_packets_over_air.pop(i)  # drop expired packet

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
                for ch_buckets in self.lora_packet_over_air
            ]

        def snapshot_remaining_wur(self) -> list:
            return [p.toa_left for p in self.wur_packets_over_air]

        def __str__(self) -> str:
            return str(self.snapshot_remaining_toa())




