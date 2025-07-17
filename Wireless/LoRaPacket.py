
class LoRaPacket:
    def __init__(self, generation_ime: int, payload: dict, header: dict):
        self.Source: str = header["source"]
        self.Destination: str = header.get("destination", "brodcast")
        self.ID: str = self.Source + self.Destination + str(generation_ime)
        self.GenerationTime: int = generation_ime
        self.ReceptionTime: int = -1 # Undefined
        self.Payload: dict = payload
        self.Header: dict = header
        self.Segments_required: int

    def set_reception_time(self, time: int):
        self.ReceptionTime = time
