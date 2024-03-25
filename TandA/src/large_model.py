import numpy as np
import pandas as pd
from abc import ABC, abstractmethod
from dataclasses import dataclass

fuel_reference_df = pd.DataFrame

@dataclass
class Fuel:

    name: str #For the time being, could be methane (ch4), carbon (co2), nitrous oxide (n2o)
    
    #WtT
    WtT_emission_factor: float

    #TtW
    emission_factor: float
    global_warming_potential: float
    is_slip: int=0 #Used as a truthy flag and a factor for a product

    def __post_init__(self):
        self.combusted_ef = self.emission_factor * self.global_warming_potential
        self.slipped_ef = (self.global_warming_potential * self.is_slip) if self.is_slip else 0

@dataclass
class Engine:

    name: str
    fuels_used: list[str]

@dataclass
class Ship:

    name: str
    fuels: list[Fuel] #TODO Add a Fuel Object | Engine Object? 
    engines : list[Engine]


class ShipEmissionCalculator(ABC):
    def __init__(self, 
                 fuel_mass: np.ndarray,
                 fuel_is_column: bool=False,
                 reward_factor: np.ndarray=1) -> None:
        
        self.fuel_mass = fuel_mass
        self.reward_factor = reward_factor
        self.fuel_is_column = fuel_is_column

    @abstractmethod
    def compute(self) -> pd.DataFrame:
        pass

class WtTCalculator(ShipEmissionCalculator):

    def __init__(self, fuel_mass: np.ndarray, fuel_is_column: bool=False, reward_factor: np.ndarray=1) -> None:
        super().__init__(fuel_mass, fuel_is_column, reward_factor)

        if self.fuel_mass.ndim > 1: #If fuel mass is by engine by fuel, reduces to only fuel dimension
            
            axis = 1
            if self.fuel_is_column:
                axis = 0
            self.fuel_mass = np.sum(self.fuel_mass, axis=axis)

    def compute(self,
                co2_intensity: np.ndarray, #1D, per fuel i
                energy_intensity: np.ndarray #1D, per fuel i
                ) -> float:
        
        #For 2 1D vector, a @ b is equivalent to np.sum(a * b)
        numerator = (self.fuel_mass * energy_intensity) @ co2_intensity #Scalar
        denominator = (self.fuel_mass * self.reward_factor) @ energy_intensity #Scalar

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

