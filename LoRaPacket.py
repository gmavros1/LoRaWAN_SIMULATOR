
class LoRaPacket:
    def __init__(self, source: str, destination: str, generation_ime: int, payload: dict, header: dict):
        self.ID = source + destination + str(generation_ime)
        self.Source = source
        self.Destination = destination
        self.GenerationTime = generation_ime
        self.ReceptionTime = None
        self.Payload = payload
        self.Header = header

    def set_reception_time(self, time: int):
        self.ReceptionTime = time
