import json
from sim.entities import BaseEntity

def load_scenario(path):

    with open(path) as f:
        data = json.load(f)

    entities = [BaseEntity(e) for e in data]

    ego = None

    for e in entities:
        if e.type == "car":
            ego = e
            break

    return entities, ego