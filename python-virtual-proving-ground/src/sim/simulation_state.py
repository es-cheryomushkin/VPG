class SimulationState:
    """
    Holds all information related to simulation state.
    This includes:
    - entities: list of all cars and pedestrians in the scenario (including ego car with index
    - controlledCar: reference to the ego car (first car in entities list)
    - roads: list of roads in the scenario (currently used for visualization only)
    - background: background image file name
    - collisions: list of current collisions (list of tuples of colliding entities)
    - engine: physics engine instance
    - scenario_files: list of scenario file paths
    - scenario_index: index of current scenario in scenario_files
    - episode_time: current time in the episode (resets to 0 when new scenario)
    - mode: "manual" or "ai" (affects control input handling)
    - headless: if True, runs without rendering (for faster testing)
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
