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
