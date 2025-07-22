import json
from collections import deque
from Wireless.signals import OOKRZWirelessSignal, Location, WakeUpBeacon
from Utils import Computations


class WakeUpRadioModule:
    """
        Continuous-time analog-correlator WuRx / RZ-OOK transmitter.
        Loads all RF parameters from the JSON spec file.
        """

    def __init__(self, id: str, parameters_path: str, position: Location):
        self.ID: str = id
        self.location = position

        # ----------------------------------------------------------------
        # Load parameters from the JSON spec
        # ----------------------------------------------------------------
        with open(parameters_path) as f:
            p = json.load(f)

        self.CenterFreq_MHz = p["center_frequency_MHz"]
        self.RX_Bandwidth_MHz = p["bandwidth_MHz"]
        self.Modulation = p["modulation"]  # “RZ-OOK”
        self.CodeLen_bits = p["code_length_bits"]  # 11
        self.Sensitivity_dBm = p["sensitivity_dBm"]  # −80.9
        self.Latency_ms = p["latency_ms"]  # 110
        self.PowerTX_dBm = p["transmission_power_dBm"]  # 14
        self.FalseAlarmRate_hr = p["false_alarm_rate_per_hour"]
        self.MissProb = p["missed_detection_ratio_at_sensitivity"]

        # runtime state ---------------------------------------------------
        self.TX_Buffer: deque[WakeUpBeacon] = deque()  # beacons to send
        self.IRQ: bool = False  # goes high when code matched
        self._latency_counter: int = 0  # ms left before IRQ


    def generate_beacon(self, generation_time: int) -> None:
        self.TX_Buffer.append(WakeUpBeacon(generation_time, self.ID))

    def transmit_beacon(self) -> OOKRZWirelessSignal | None:
        """Pop first beacon (if any) and wrap it in a WirelessSignal."""
        if self.TX_Buffer:
            return OOKRZWirelessSignal(self.TX_Buffer.popleft(), self, self.Latency_ms)
        return None

    def listen(self, environment) -> None:
        """
        Scan environment for beacons on our channel.
        If a beacon’s RX power ≥ sensitivity, start latency timer.
        """
        beacons = environment.wur_packets_over_air
        for sig in beacons:
            rx_power = Computations.calculate_received_power(
                Computations.distance(sig.signal.source_location, self.location), sig.signal.tx_power_dBm)
            # check sensitivity
            if rx_power >= self.Sensitivity_dBm and sig.toa_left == self.Latency_ms:
                # start / refresh latency counter
                self._latency_counter = self.Latency_ms

        # countdown latency counter
        if self._latency_counter > 0:
            self._latency_counter -= 1
            if self._latency_counter == 0:
                self.IRQ = True  # wake-up event!
                # print("WAKE UP SIGNAL")
        else:
            self.IRQ = False

    # convenience --------------------------------------------------------
    def __repr__(self) -> str:
        return (f"<WuRx {self.ID} @ {self.CenterFreq_MHz} MHz "
                f"Sens {self.Sensitivity_dBm} dBm IRQ={self.IRQ}>")