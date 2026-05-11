import json
from sim.entities import BaseEntity
from sim.road import Road

class SimulationState:
    """
    Holds all information related to simulation state.
    """
    def __init__(self):
        self.entities = []
        self.controlled_car = None
        self.roads = []
        self.background = None
        self.collisions = []

        self.engine = None
        self.scenario_files = []

        self.scenario_index = 0
        self.episode_time = 0.0

        self.mode = "manual"
        self.headless = False

def load_scenario(path):
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

    # =====================================================
    # MODERN SCENARIO FORMAT
    # =====================================================
    if isinstance(data, dict):

        name = data.get("name")
        description = data.get("description")

        background = data.get("background")

        entities_data = data.get("entities", [])
        roads_data = data.get("roads", [])

        roads = [Road(r) for r in roads_data]

    # =====================================================
    # LEGACY FORMAT
    # =====================================================
    else:
        entities_data = data

    # =====================================================
    # ENTITIES
    # =====================================================
    entities = [BaseEntity(e) for e in entities_data]

    # =====================================================
    # EGO CAR
    # =====================================================
    ego = None

    for e in entities:

        if e.type == "car":
            ego = e
            break

    return (
        entities,
        roads,
        ego,
        background,
        name,
        description
    )