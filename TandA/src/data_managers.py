import pandas as pd
from abc import ABC, abstractmethod
from pathlib import Path

class DataLoader(ABC):

    @abstractmethod   
    def load_data(self, path: str | Path) -> pd.DataFrame:
        pass

    def suffix_adder(self, path: Path, suffix: str) -> Path:

        suffix = '.'.join(('', suffix))
        if not (path.suffix == suffix):
            path = path.with_suffix(suffix)
        
        return path
    
    def converts_to_path(self, path: str | Path) -> Path:
        if isinstance(path, str): 
            path = Path(path)
        
        return path


class ParquetDataLoader(DataLoader):
    def load_data(self, path: str | Path) -> pd.DataFrame:
        
        path = self.converts_to_path(path)
        path = self.suffix_adder(path, 'csv')
        return pd.read_parquet(path)

class CSVDataLoader(DataLoader):
    def load_data(self, path: str | Path) -> pd.DataFrame:
        
        path = self.converts_to_path(path)
        path = self.suffix_adder(path, 'parquet')
        return pd.read_csv(path)

class DataSaver(ABC):
    @abstractmethod
    def save_data(self, df: pd.DataFrame, path: str) -> None:
        pass

    def suffix_adder(self, path: Path, suffix: str) -> Path:

        suffix = '.'.join(('', suffix))
        if not (path.suffix == suffix):
            path = path.with_suffix(suffix)
    
        return path
    
    def converts_to_path(self, path: str | Path) -> Path:
        if isinstance(path, str): 
            path = Path(path)
        
        return path

class ParquetDataSaver(DataSaver):
    def save_data(self, df: pd.DataFrame, path: str) -> None:
        df.to_parquet(path)

class CSVDataSaver(DataSaver):
    def save_data(self, df: pd.DataFrame, path: str) -> None:
        df.to_csv(path)

#####################################################################
