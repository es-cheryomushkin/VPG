import json
from sim.entities import BaseEntity

def load_scenario(path):
    with open(path) as f:
        data = json.load(f)
    name = None
    description = None

    if isinstance(data, dict):
        name = data.get("name")
        description = data.get("description")
        entities_data = data.get("entities", [])
    else:
        entities_data = data

    entities = [BaseEntity(e) for e in entities_data]

    ego = None
    for e in entities:
        if e.type == "car":
            ego = e
            break

    return entities, ego, name, description