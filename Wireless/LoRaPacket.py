
class LoRaPacket:
    def __init__(self, generation_ime: int, payload: dict, header: dict, segment_counter: int):
        self.Source: str = header["source"]
        self.Destination: str = header.get("destination", "brodcast")
        self.ID: str = self.Source + self.Destination + str(generation_ime)
        self.GenerationTime: int = generation_ime
        self.ReceptionTime: int = -1 # Undefined
        self.Payload: dict = payload
        self.Header: dict = header
        self.segment_counter: int = segment_counter
        self.Segments_required: int
        self.IsFirstPacket: bool = True

        # Helper ----------
        self.sf: int = 0
        self.channel: int = 0

    def set_reception_time(self, time: int):
        self.ReceptionTime = time
