import random
import time


def maybe_sleep(p: float = 0.5, low: float = 0.05, high: float = 0.8) -> None:
    if random.random() < p:
        time.sleep(random.uniform(low, high))
