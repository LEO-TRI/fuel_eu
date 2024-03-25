import numpy as np
import pandas as pd
from abc import ABC, abstractmethod
from dataclasses import dataclass
import functools as ft

fuel_reference_df = pd.DataFrame
slip_fuels: set = set(("ch4",)) #TODO: What to do with this?

@dataclass
class PowerSource:
    
    name: str
    emission_factor: float

@dataclass
class Fuel(PowerSource):

    name: str #For the time being, could be methane (ch4), carbon (co2), nitrous oxide (n2o)
    lower_calorific_value: float
    is_non_biological: bool=True

    #WtT
    #emission_factor: float

    #TtW
    global_warming_potential: float
    slip_factor: int=0 #Used as a truthy flag and a factor for a product -> For now, only methane can slip with factor 1

    combusted_ef: float=None #Not defined bc requires an engine type as well

    def __post_init__(self):
        self.slipped_ef: float=self.global_warming_potential * self.slip_factor
        self.reward_factor: int=(self.is_non_biological + 1) if self.is_non_biological else int(self.is_non_biological)

@dataclass
class Electricity(PowerSource):
    
    is_green_electricity: bool=True

    def __post_init__(self):
        self.emission_factor = 0 if self.is_green_electricity else self.emission_factor #Introduced since elec ef is assumed to be always 0 for FuelEU


@dataclass
class PowerGenerator(ABC):
    
    name : str
    fuels_used: list[Fuel] | Electricity

@dataclass
class Engine(PowerGenerator):

    kind: str = "engine"

    #TtW
    slip_rate: float

    fuel_engine_table: pd.DataFrame

    def __post_init__(self):

        self.slip_rate = (self.slip_rate / 100) if (self.slip_factor >= 1) else self.slip_rate #Corrects potential error if slip rate is passed in %
        self.combusted_ef_list = [(self.fuel_engine_table.at[self.name, fuel.name] * fuel.global_warming_potential) for fuel in self.fuels_used]
        self.slipped_ef_list = [fuel.slipped_ef for fuel in self.fuels_used]

@dataclass
class ElectricPort(PowerGenerator):
    
    kind: str = "electricity"    
    
    def __post_init__(self):

        self.fuels_used = [self.fuels_used] if (not isinstance(self.fuels_used, list)) else self.fuels_used


@dataclass
class Ship:

    name: str
    engines: list[Engine | ElectricPort]
    ship_ef: float = 1

    def __post_init__(self):
        self.fuels_used = list(set().union(*[engine.fuels_used for engine in self.engines])) #Indicative, fuels are allocated via the Engine class

#TODO: Add subclasses of ships?
        

class ShipEmissionCalculator(ABC):
    def __init__(self, 
                 ship: Ship,
                 fuel_mass_per_engine: list[pd.Series],
                 ) -> None:

        self.ship = ship
        
        self.fuel_engine_table = pd.DataFrame(index=[fuel.name for fuel in self.ship.fuels_used])
        #Recursive left joins to create a comprehensive table of fuels vs engines consumption
        self.fuel_engine_table = (ft.reduce(lambda x,y: x.join(y.to_frame(name=y.name), how="left"), 
                                            (self.fuel_engine_table, *fuel_mass_per_engine)
                                            )
                                    .replace(np.nan, 0)
                                    )
        #self.fuel_mass_per_engine = fuel_mass_per_engine

    @abstractmethod
    def compute(self) -> pd.DataFrame:
        pass

class WtTCalculator(ShipEmissionCalculator):

    def __init__(self, ship: Ship, fuel_mass_per_engine: list[pd.Series]) -> None:
        
        super().__init__(ship, fuel_mass_per_engine)

        self.fuel_engine_table = (self.fuel_engine_table.sum(axis=1) #Erasing the engine dimension for WtT.
                                                        .to_frame(name="fuelsUsed")
                                                        )
        self.fuel_factors = (pd.DataFrame(data=[(fuel.name, fuel.lower_calorific_value, fuel.WtT_emission_factor, fuel.reward_factor) for fuel in self.ship.fuels_used], 
                                          columns=["fuels", "lowerCalorificValue", "emisssionFactorWtT", "rewardFactor"]
                                          )
                                .set_index('fuels')
                                )
        self.fuel_engine_table = self.fuel_engine_table.join(self.fuel_factors, how="left")


    def compute(self) -> float:

        fuels_used = self.fuel_engine_table["fuelsUsed"].to_numpy()
        lcv = self.fuel_engine_table["lowerCalorificValue"].to_numpy()
        ef_WtT = self.fuel_engine_table["emisssionFactorWtT"].to_numpy()
        reward_factor = self.fuel_engine_table["rewardFactor"].to_numpy()
        
        #For 2 1D vector, a @ b is equivalent to np.sum(a * b)
        numerator = (fuels_used * ef_WtT) @ lcv #Scalar
        denominator = (fuels_used * reward_factor) @ lcv #Scalar

        return numerator / denominator

class TtWCalculator(ShipEmissionCalculator):

    def __init__(self, fuel_mass: np.ndarray, fuel_is_column: bool=False, reward_factor: np.ndarray=1) -> None:
        
        super().__init__(fuel_mass, fuel_is_column, reward_factor)

    def compute(self,
                co2_intensity_consumed: np.ndarray, #2D, fuel i and engine j 
                co2_intensity_slipped : np.ndarray, #2D, fuel i and engine j 
                slips: np.ndarray, #1D, per engine j
                energy_intensity: np.ndarray #1D, per fuel i
                ) -> float:
        
        #co2_emissions_per_mass_of_fuel_per_engine = np.diagonal(fuel_mass.T @ co2_emissions_per_fuel_per_engine) 
        #co2_emissions_total = np.sum(co2_emissions_per_mass_of_fuel_per_engine)

        fuel_mass = self.fuel_mass.copy()

        #Transpose the 2D arrays if fuels are rows and engines columns
        if self.fuel_is_column: 
            co2_intensity_consumed = co2_intensity_consumed.T
            co2_intensity_slipped = co2_intensity_slipped.T
            fuel_mass = fuel_mass.T

        co2_emissions_per_fuel_per_engine = ((1 - slips) * co2_intensity_consumed) + (slips * co2_intensity_slipped) #2D Array
        co2_emissions_total = np.sum(fuel_mass * co2_emissions_per_fuel_per_engine, axis=None) #Scalar

        denominator = (np.sum(fuel_mass, axis = 1) * self.reward_factor) @ energy_intensity #Scalar

        return co2_emissions_total / denominator

