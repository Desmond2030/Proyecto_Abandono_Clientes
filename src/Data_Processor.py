import sys
import os

sys.path.append(os.path.abspath(os.path.join('..')))

import pandas as pd
import numpy as np


from src.Data_Loader import DataLoader
from src.Graficos import Graficos


class DataProcessor(DataLoader):
    def __init__(self):
        super().__init__()
        self.graficos = Graficos()
        
    
    def set_types(self, tipos:dict ) -> 'DataProcessor':
        self._data = self._data.astype(tipos)
        return self
    


    
    
    def replace_to_numeric_bool(self,
                     columnas:list,
                     map:dict = {},
                     replace = None,
                     *args,
                     **kargs) -> 'DataProcessor':
        
        if replace:
            for col in columnas:
                self._data[col] = self._data[col].replace(*args, **kargs)
        
        for columna in columnas:
            self._data[columna] = self._data[columna].map(map).astype(int)
        return self
    
    




    def set_categorical_columns(self, 
                                columna: str, 
                                categorias: list = None, 
                                cat_codes:bool = False, 
                                *args, 
                                **kargs) -> 'DataProcessor':
        
        
        
        categories = pd.api.types.CategoricalDtype(
            categories = categorias if categorias else list(self._data[columna].unique()), 
            *args,
            **kargs
        )
       
        self._data[columna] = self._data[columna].astype(categories)
        
        if cat_codes:
            self._data[columna] = self._data[columna].cat.codes
        
        return self
    

    
    def get_dummies(self, 
                    columna: str, 
                    prefijo:str, 
                    categorias: list = None,
                    drop_dummie:list = None,
                    *args, 
                    **kargs) -> 'DataProcessor':
        
        
        self.set_categorical_columns(columna, *args, **kargs)
        
        dummies = pd.get_dummies(self._data[columna], prefix=prefijo, dtype=np.int8)
        dummies_columns = []
        
        for categoria in list(self._data[columna].unique()):
            dummies_columns = [col for col in dummies.columns if col != f"{prefijo}_{categoria}"]
            
        dummies = dummies[dummies_columns].copy()
        print(dummies.columns)
        
        idx = self._data.columns.get_loc(columna)
        
        for i, col_name in enumerate(dummies.columns):
            self._data.insert(loc=idx + i, column=col_name, value=dummies[col_name])
        
        self._data.drop(columns=[columna], inplace=True) 
        
        if drop_dummie:
            self._data.drop(columns=drop_dummie, inplace=True)
        
        return self



