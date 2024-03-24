import numpy as np
import pandas as pd
from abc import ABC, abstractmethod
from pathlib import Path

class DataLoader(ABC):
    @abstractmethod   
    def load_data(self, path: str | Path) -> pd.DataFrame:
        pass

class ParquetDataLoader(DataLoader):
    def load_data(self, path: str | Path) -> pd.DataFrame:
        return pd.read_parquet(path)

class CSVDataLoader(DataLoader):
    def load_data(self, path: str | Path) -> pd.DataFrame:
        return pd.read_csv(path)

class DataSaver(ABC):
    @abstractmethod
    def save_data(self, df: pd.DataFrame, path: str) -> None:
        pass

class ParquetDataSaver(DataSaver):
    def save_data(self, df: pd.DataFrame, path: str) -> None:
        df.to_parquet(path)

class CSVDataSaver(DataSaver):
    def save_data(self, df: pd.DataFrame, path: str) -> None:
        df.to_csv(path)

#####################################################################
        

class FuelCalculator(ABC):
    
    fuel_reference_table = fuel_reference_table

    def __init__(self, fuel_reference_table) -> None:

        self.fuel_reference_table = fuel_reference_table

    @abstractmethod
    @staticmethod
    def compute_fuel_emission(fuel: str):
        pass

class WtTFuelCalculator(FuelCalculator):

    def compute_fuel_emission(fuel_mass: float, fuel_ef: float, fuel_calorific_value: float) -> float:

        return fuel_ef * fuel_mass * fuel_calorific_value

class TtWFuelCalculator(FuelCalculator):

    def compute_fuel_emission(fuel_mass: float, fuel_ef_combusted: float, fuel_ef_slippped: float, slip_rate: float) -> float:

        return (
            (fuel_ef_combusted * (1 - slip_rate) + slip_rate * fuel_ef_slippped) * fuel_mass
                )

class ShipEmissionCalculator(ABC):
    pass


class GHGFuelSimulator:

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
    


    
    