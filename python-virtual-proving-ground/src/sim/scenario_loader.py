import json
from sim.entities import BaseEntity
from sim.road import Road
from src.sim.scenario import Scenario

def load_scenario(path: str):
    """
    Loads full scenario:
    - entities
    - roads
    - background

    First car becomes ego vehicle.
    """

    with open(path) as f:
        data = json.load(f)

    name = None
    description = None

    roads = []
    background = None


    if isinstance(data, dict):
        # MODERN SCENARIO FORMAT
        name = data.get("name")
        description = data.get("description")

        background = data.get("background")

        entities_data = data.get("entities", [])
        roads_data = data.get("roads", [])

        roads = [Road(r) for r in roads_data]

    else:
        # LEGACY FORMAT
        entities_data = data

    # =====================================================
    # ENTITIES
    # =====================================================
    entities = [BaseEntity(e) for e in entities_data]
    ego = None

    for e in entities:

        if e.type == "car":
            ego = e
            break

    return Scenario(
        entities,
        roads,
        ego,
        background,
        name,
        description
    )