
class LoRaPacket:
    def __init__(self, generation_ime: int, payload: dict, header: dict):
        self.ID: str = header["source"] + header["destination"] + str(generation_ime)
        self.Source: str = header["source"]
        self.Destination: str = header["destination"]
        self.GenerationTime: int = generation_ime
        self.ReceptionTime: int = -1 # Undefined
        self.Payload: dict = payload
        self.Header: dict = header

    def set_reception_time(self, time: int):
        self.ReceptionTime = time
