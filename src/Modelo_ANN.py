import sys
import os

# Agrega la carpeta raíz del proyecto al path de Python
sys.path.append(os.path.abspath(os.path.join('..')))

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense, Activation, Input
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.callbacks import EarlyStopping
from tensorflow.keras.layers import Dropout
from tensorflow.keras.callbacks import TensorBoard
from sklearn.metrics import classification_report,confusion_matrix
from sklearn.utils.class_weight import compute_class_weight
from keras.metrics import Precision, Recall, AUC
import pickle
from abc import ABC, abstractmethod


from src.Data_Processor import DataProcessor



class Modelo_ANN(DataProcessor, ABC):
    def __init__(self, 
                 x_train_file_name:str, 
                 y_train_file_name:str, 
                 x_test_file_name:str, 
                 y_test_file_name:str,
                 val_file_name:str,
                 data_paths:list):
        
        
        DataProcessor.__init__(self)
        self.x_train_file_name = x_train_file_name
        self.y_train_file_name = y_train_file_name
        self.x_test_file_name = x_test_file_name
        self.y_test_file_name = y_test_file_name
        
        self.val_file_name:str = val_file_name
        
        self.data_paths = data_paths
        
        self._partitions: dict = {}
        self._model = Sequential()
        
        self._predictions = None
    


    @property
    def partitions(self):
        return self._partitions

    @property
    def model(self):
        return self._model
    
    @model.setter
    def model(self, model):
        self._model = model

    def set_partitions(self, *pd_args, **pd_kwargs):
        
        file_names = [self.x_train_file_name,
                      self.y_train_file_name,
                      self.x_test_file_name,
                      self.y_test_file_name,
                      self.val_file_name]

        for path, file_name in zip(self.data_paths, file_names):
            if file_name:
                self.load_data(path, *pd_args, **pd_kwargs)
                self._partitions[file_name] = self._data.astype('float64')
                
                
        return self
    
                 
    def set_val_data_as_data(self):
        if self.val_file_name:
            self._data = self.partitions[self.val_file_name]
        else:
            raise ValueError("Sin data para validacion")
        return self



    

    def model_flow_settings(self, 
                            capas:int, 
                            fun_act:str,
                            loss:str,
                            optimizer:str,
                            n_output:int,
                            dropout:float= None,
                            fun_out:str= None,
                            reset_model=None):
        
        if reset_model:
            self._model = Sequential()
            
        num_neuronas = self._partitions[self.x_train_file_name].shape[1]
            
        self._model.add(Dense(units=num_neuronas,activation=fun_act))
        
        while capas != 0:
            capas -= 1
            self._model.add(Dense(units=num_neuronas,activation=fun_act))
            if dropout:
                self._model.add(Dropout(dropout))
    
    
        self._model.add(
            Dense(units=n_output,
                  activation= fun_out if fun_out else fun_act))
        
        self._model.compile(loss=loss, 
                            optimizer=optimizer, 
                            metrics = [
                                Precision(), 
                                Recall(), 
                                AUC()
                                ]
                            )
        
        return self
        

    
    def start_training(self,
                       epochs:int,
                       early_stop = None,
                       w_balance = 'balanced',
                       w_dict = None,
                       *early_stop_args,
                       **early_stop_kargs):
    
        clases_unicas = np.unique(self._partitions[self.y_train_file_name])
        pesos_calculados = compute_class_weight(
            class_weight= w_balance, 
            classes=clases_unicas, 
            y=self._partitions[self.y_train_file_name]
        )
        
        diccionario_pesos = w_dict if w_dict else dict(zip(clases_unicas, pesos_calculados))
    
        if early_stop:
            self._model.fit(
                x=self._partitions[self.x_train_file_name],
                y=self._partitions[self.y_train_file_name],
                validation_data=(self._partitions[self.x_test_file_name], self._partitions[self.y_test_file_name]),
                epochs=epochs,
                callbacks=[
                    EarlyStopping(
                        *early_stop_args,
                        **early_stop_kargs
                        )
                        ],
                class_weight=diccionario_pesos
            )
        else:
            self._model.fit(
                x=self._partitions[self.x_train_file_name],
                y=self._partitions[self.y_train_file_name],
                validation_data=(self.x_test_file_name, self.y_test_file_name),
                epochs=epochs,
                class_weight=diccionario_pesos
            )
        
        return self
    
    
        @abstractmethod
        def make_prediction(self, 
                        data = None, 
                        target:str = None, 
                        new_data = None,
                        eval= None):
            
            pass
    
    
    
class Binary_Model(Modelo_ANN):
    def __init__(self, 
                 x_train_file_name:str, 
                 y_train_file_name:str, 
                 x_test_file_name:str, 
                 y_test_file_name:str,
                 val_file_name:str,
                 data_paths:list):
        super().__init__(
            x_train_file_name, 
            y_train_file_name, 
            x_test_file_name, 
            y_test_file_name,
            val_file_name,
            data_paths)
    
    def make_prediction(self, 
                        data = None, 
                        target:str = None, 
                        new_data = None,
                        eval= None):
        
        if new_data:
            self._data = data
        else:
            self.set_val_data_as_data()
 
        inputs = self._data.drop(target, axis=1) if target in self.data.columns else self._data
        outputs = self._data[target] if target in self._data.columns else 0

        inputs = self._scaler.transform(inputs)
        
        resultado = (self.model.predict(inputs) < 0.5).astype("int32")
        
        self._predictions = pd.DataFrame(resultado)
        
        self._data[f"Prediccion_{target}"] = self._predictions
        
        if eval:
            
            reporte_clasificacion = classification_report(
                self._data[target],
                self._data[f"Prediccion_{target}"])
            
            matriz_confucion = confusion_matrix(
                self._data[target],
                self._data[f"Prediccion_{target}"])
            
            print("Reporte de clasificacion:\n",reporte_clasificacion, "\n")
            print("Matriz de confucion:\n",matriz_confucion)

        
        return self
    

        
        

