import numpy as np
import pandas as pd
from abc import ABC, abstractmethod

class ShipCalculator(ABC):
    def __init__(self, reward_factor: np.ndarray=1) -> None:
        self.reward_factor = reward_factor

    @abstractmethod
    def compute(self, df: pd.DataFrame) -> pd.DataFrame:
        pass

class WtTCalculator(ShipCalculator):

    def compute(self,
                fuel_mass: np.ndarray, 
                co2_intensity: np.ndarray, 
                energy_intensity: np.ndarray) -> np.ndarray:
        
        if fuel_mass.ndim > 1: #If fuel mass is by engine by fuel, reduces to only fuel dimension
            fuel_mass = np.sum(fuel_mass, axis=1)

        #For 2 1D vector, a @ b is equivalent to np.sum(a * b)
        numerator = (fuel_mass * energy_intensity) @ co2_intensity
        denominator = (fuel_mass * self.reward_factor) @ energy_intensity

        return numerator / denominator

class TtWCalculator(ShipCalculator):

    def compute(self,
                fuel_mass: np.ndarray, 
                co2_intensity_consumed: np.ndarray, 
                co2_intensity_slipped : np.ndarray, 
                slips: np.ndarray,
                energy_intensity: np.ndarray) -> np.ndarray:
        
        #co2_emissions_per_mass_of_fuel_per_engine = np.diagonal(fuel_mass.T @ co2_emissions_per_fuel_per_engine) 
        #co2_emissions_total = np.sum(co2_emissions_per_mass_of_fuel_per_engine)

        co2_emissions_per_fuel_per_engine = ((1 - slips) * co2_intensity_consumed) + (slips * co2_intensity_slipped) #2D Array
        co2_emissions_total = np.sum(fuel_mass * co2_emissions_per_fuel_per_engine, axis=None) #Scalar

        denominator = (np.sum(fuel_mass, axis = 1) * self.reward_factor) @ energy_intensity

        return co2_emissions_total / denominator
