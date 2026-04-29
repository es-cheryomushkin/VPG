import json
from sim.entities import BaseEntity

class SimulationState:
    """
    Holds all information related to simulation state.
    """
    def __init__(self):
        self.entities = []
        self.controlled_car = None
        self.engine = None
        self.scenario_files = []
        self.scenario_index = 0
        self.episode_time = 0.0
        self.mode = "manual"
        self.headless = False

def load_scenario(path):
    """
    Loads scenario by cycling through all entities. Gets first car class as ego car.
    """
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