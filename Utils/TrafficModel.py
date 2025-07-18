import random


class TrafficModel:
    def __init__(self):
        self.probability: float = 0.05

    def event_happened(self) -> bool:
        if random.uniform(0, 1) < self.probability:
            return True
        return False