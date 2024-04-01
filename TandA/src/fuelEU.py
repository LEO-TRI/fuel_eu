import numpy as np
import pandas as pd
import itertools as it
from abc import ABC, abstractmethod
from pathlib import Path
from large_model import Ship

#####################################################################

class GHGFuelSimulator(ABC):

    def __init__(self, prop_wind_proportion: float=0) -> None:
        
        self.reward_wind = 1
        if 0.05 < prop_wind_proportion <= 0.1:
            self.reward_wind = 0.99
        elif 0.1 < prop_wind_proportion <= 0.15:
            self.reward_wind = 0.97
        elif 0.15 < prop_wind_proportion:
            self.reward_wind = 0.95 

    def calcuate_ghg_intensity(self, emissions_WtT: float, emissions_TtW: float, wind_reward_factor: float=1.):

        return (emissions_WtT + emissions_TtW) * wind_reward_factor

class ShipConverter(ABC):

    def __init__(self) -> None:
        pass

    def convert(self, 
                ships: list[Ship], 
                ship_attributes: list[str], 
                engines_attributes: list[str]
                ) -> pd.DataFrame:
        
        #gen_a = (self.get_attribute_values(ship, ship_attributes) for ship in ships)
        #gen_b = (self.processing_engines(ship, engines_attributes) for ship in ships)
        #c = it.chain.from_iterable([([tuple(a+x) for x in b] for (a, b) in zip(gen_a, gen_b)])

        if isinstance(ship_attributes, str):
            ship_attributes = [ship_attributes]
        if isinstance(engines_attributes, str):
            engines_attributes = [engines_attributes]

        if not ('name' in ship_attributes):
            ship_attributes.append('name')
        
        ships_df = (pd.DataFrame((self.get_attribute_values(ship, ship_attributes) for ship in ships),
                                 columns=ship_attributes)
                      .set_index('name')
                      )     
        gen_engines = ((pd.DataFrame(data=self.processing_engines(ship, engines_attributes), #list[tuples]
                                     columns=engines_attributes,
                                     index=np.full(len(ship.engines), ship.name))
                         ) 
                         for ship in ships
                         )
        engines_df = pd.concat(gen_engines, axis=0)
        merged_df = (engines_df.join(ships_df, how='left', lsuffix='_engine', rsuffix='_ship')
                               .reset_index()
                               .loc[:, ship_attributes + engines_attributes])
        
        return merged_df
        
    def processing_engines(self, ship: Ship, engines_attributes: list[str]) -> list[list]:
        return [self.get_attribute_values(engine, engines_attributes) for engine in ship.engines]

    @staticmethod
    def get_attribute_values(obj, attribute_names: list[str]) -> list:
        return list((getattr(obj, name) for name in attribute_names))


class FleetEmissionCalculator(GHGFuelSimulator):

    def __init__(self, ship_df: pd.DataFrame, 
                 fuel_table: pd.DataFrame,
                 merge_column: str="fuel", 
                 prop_wind_proportion: float=0):

        super.__init__(prop_wind_proportion)

        self.ship_table = (ship_df.join(fuel_table, how='left')
                                          .reset_index()
                                          .set_index(['imo', 'engine'])
                                          )
    
    
    def compute_WtT(self):
        pass
            





    