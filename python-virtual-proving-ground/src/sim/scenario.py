from src.scenario_creator import Road
from src.sim.entities import BaseEntity


class Scenario:
    """
    Представляет загруженный сценарий симуляции.
    """
    def __init__(self, entities: list[BaseEntity], roads: list[Road],
                 background: str, name: str, description: str, ):
        self.name = name     
        """ Scenario name """          
        self.description = description  
        """ Scenario description """        
        self.entities = entities      
        """ All cars or pedestrians in scenario (including ego car with index 0) """ 
        self.roads = roads     
        """ Roads that are displayed on map. Currently used for visualization only"""              
        self.background = background  
        """ Backgound image file name"""

        """
    return Scenario(
        entities,
        roads,
        background,
        name,
        description
    )"""

    @property
    def ego(self):
        """ Ego car (our target car with autonomous driving strategy) """
        return self.entities[0]