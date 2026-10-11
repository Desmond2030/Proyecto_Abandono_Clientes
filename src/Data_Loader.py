import sys
import os

sys.path.append(os.path.abspath(os.path.join('..')))

import pandas as pd
import numpy as np
import openpyxl


class DataLoader:
    def __init__(self):
        self._data = None
        self._array = None
    
    @property
    def data(self):
        return self._data
    
    @data.setter
    def data(self, data):
        self._data = data
        
        
        
    @property
    def array(self):
        return self._array
    
    @array.setter
    def array(self, array):
        self._array = self._array
        
    
    
    def load_data(self, file_path, *pd_args, **pd_kwargs) -> None:
        if file_path.endswith('.csv'):
            self._data = pd.read_csv(file_path, *pd_args, **pd_kwargs)
        elif file_path.endswith('.xlsx'):
            self._data = pd.read_excel(file_path, *pd_args, **pd_kwargs)
        elif file_path.endswith('.parquet'):
            self._data = pd.read_parquet(file_path, *pd_args, **pd_kwargs)
        else:
            raise ValueError("Usar extencion .csv, .xlsx, o .parquet")
        
        return self
    
    
        
    def save_data(self, file_path, *args, **kargs):
        if file_path.endswith('.csv'):
            self._data.to_csv(file_path, *args, **kargs)
        elif file_path.endswith('.xlsx'):
            self._data.to_excel(file_path, *args, **kargs)
        elif file_path.endswith('.parquet'):
            self._data.to_parquet(file_path, *args, **kargs)
        elif file_path.endswith('.npy'):
            np.save(file_path, self.array)
        else:
            raise ValueError("Usar extencion .npy, .csv, .xlsx o .parquet")
    
