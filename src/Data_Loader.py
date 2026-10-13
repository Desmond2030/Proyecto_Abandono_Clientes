import sys
import os

sys.path.append(os.path.abspath(os.path.join('..')))

import pandas as pd
import numpy as np
import openpyxl
from sklearn.preprocessing import MinMaxScaler
import pickle

class DataLoader:
    def __init__(self):
        self._data = None
        self._scaler = MinMaxScaler()
        
        
    @property
    def scaler(self):
        return self._scaler
    
    @scaler.setter
    def scaler(self, scaler):
        self._scaler = scaler 
    
    @property
    def data(self):
        return self._data
    
    @data.setter
    def data(self, data):
        self._data = data
        
        

        
    
    
    def load_data(self, file_path, *pd_args, **pd_kwargs) -> None:
        
        
        if file_path.endswith('.csv'):
            self._data = pd.read_csv(file_path, *pd_args, **pd_kwargs)
        elif file_path.endswith('.xlsx'):
            self._data = pd.read_excel(file_path, *pd_args, **pd_kwargs)
        elif file_path.endswith('.parquet'):
            self._data = pd.read_parquet(file_path, *pd_args, **pd_kwargs)
        else:
            raise ValueError("Usar extencion .csv, .xlsx o .parquet")
        
        return self
    
    
        
    def save_data(self, file_path, *pd_args, **pd_kwargs):
        if file_path.endswith('.csv'):
            self._data.to_csv(file_path, *pd_args, **pd_kwargs)
        elif file_path.endswith('.xlsx'):
            self._data.to_excel(file_path, *pd_args, **pd_kwargs)
        elif file_path.endswith('.parquet'):
            self._data.to_parquet(file_path, *pd_args, **pd_kwargs)
        else:
            raise ValueError("Usar extencion .csv, .xlsx o .parquet")
        
        return self
    


    def save_load_scaler(self, path, save = None, load = None):
        if save:
            with open(path, 'wb') as archivo:
                pickle.dump(self._scaler, archivo)
                
        if load:
            with open(path, 'rb') as archivo:
                self._scaler = pickle.load(archivo)
                
        return self