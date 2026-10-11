import sys
import os

# Agrega la carpeta raíz del proyecto al path de Python
sys.path.append(os.path.abspath(os.path.join('..')))
import random

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import tensorflow as tf
import keras
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense, Activation, PReLU, Dropout
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.callbacks import EarlyStopping, ModelCheckpoint
from tensorflow.keras.layers import Dropout
from tensorflow.keras.callbacks import TensorBoard
from sklearn.metrics import classification_report,confusion_matrix, mean_squared_error,mean_absolute_error,explained_variance_score
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
        
    @property
    
    def predictions(self):
        return self._predictions

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


    def preparar_experimento(self,semilla):
        tf.keras.backend.clear_session()
        tf.keras.utils.set_random_seed(semilla)
        
        return self

    

    def model_flow_settings(self, 
                            capas:int, 
                            fun_act:str,
                            loss:str,
                            optimizer:str,
                            n_output:int,
                            leakyrelu_negative_slope: float = None,
                            n_down = None,
                            dropout:float= None,
                            fun_out:str= None):
        
        self._model = Sequential()
            
        num_neuronas = self._partitions[self.x_train_file_name].shape[1]
        
        

              
        if fun_act == 'LeakyReLU' and leakyrelu_negative_slope:
            fun_act = keras.layers.LeakyReLU(negative_slope=leakyrelu_negative_slope)
          
          
        if fun_act == 'PReLU' :
              self._model.add(Dense(units=num_neuronas))
              self._model.add(PReLU())  
        else:
            self._model.add(Dense(units=num_neuronas,activation=fun_act))
        
        
        neuron_decrease = num_neuronas
        while capas != 0:
            
            
            
            if n_down and int((neuron_decrease * n_down)) > n_output:
                neuron_decrease = int((neuron_decrease * n_down))
        
            
            if fun_act == 'PReLU' :
                self._model.add(Dense(units=num_neuronas))
                self._model.add(PReLU())
            else:
                self._model.add(Dense(units=neuron_decrease,activation=fun_act))
            
            if dropout and n_down:
                self._model.add(Dropout(dropout * n_down))
            elif dropout:
                self._model.add(Dropout(dropout))
                
            
    
    
            capas -= 1
    
        self._model.add(
            Dense(units=n_output,
                  activation= fun_out if fun_out else fun_act))
        
        self._model.compile(loss=loss, 
                            optimizer=optimizer, 
                            metrics = [tf.keras.metrics.AUC(curve='PR', name='prc')]
                            )
        
        return self
        

    
    def start_training(self,
                       epochs:int,
                       w_balance = True,
                       w_dict = None,
                       batch_size= None,
                       callbacks= []):
    
    
        clases_unicas= None
        pesos_calculados= None
        
        if w_balance:

            clases_unicas = np.unique(self._partitions[self.y_train_file_name])
            pesos_calculados = compute_class_weight(
                class_weight= 'balanced', 
                classes=clases_unicas, 
                y=self._partitions[self.y_train_file_name]
            )
        
        diccionario_pesos = w_dict if w_dict else dict(zip(clases_unicas, pesos_calculados))
    

        self._model.fit(
            x=self._partitions[self.x_train_file_name].to_numpy(),
            y=self._partitions[self.y_train_file_name].to_numpy(),
            validation_data=(self._partitions[self.x_test_file_name].to_numpy(), 
                             self._partitions[self.y_test_file_name].to_numpy()),
            epochs=epochs,
            batch_size=batch_size,
            callbacks=callbacks,
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

        if f"Prediccion_{target}" in inputs.columns:
            inputs = inputs.drop(f"Prediccion_{target}", axis=1)

        inputs = self._scaler.transform(inputs)
        
        resultado = (self.model.predict(inputs) > 0.8).astype("int32")
        
        self._predictions = pd.DataFrame(resultado)
        
        self._data[f"Prediccion_{target}"] = self._predictions
        
        if eval:
            
            
            mae = mean_absolute_error(
                self._data[target],
                self._predictions)
            
            mae_sqrt = np.sqrt( 
                            mean_squared_error(
                                self._data[target],
                                self._predictions
                                )
                               )
            
            
            if self._data[target].median() != 0:
                median_desv = mean_absolute_error(self._data[target], self._predictions)/self._data[target].median()
                
            if self._data[target].median() == 0:
                median_desv = "Divicion entre 0"
            
            
            if self._data[target].mean() != 0:
                mean_desv = mean_absolute_error(self._data[target], self._predictions)/self._data[target].mean()
                
            if self._data[target].mean() == 0:
                mean_desv = "Divicion entre 0"  
                
              
            
            reporte_clasificacion = classification_report(
                self._data[target],
                self._predictions)
            
            matriz_confucion = confusion_matrix(
                self._data[target],
                self._predictions)
            
            matriz_confucion = pd.DataFrame(
                matriz_confucion, 
                columns=['No abandona(predict) (0)', 'Abandona(predict) (1)'],
                index=['No abandona(real) (0)', 'Abandona(real) (1)']
            )
            
            print("Reporte de clasificacion:\n",reporte_clasificacion, "\n")
            print("Matriz de confucion:\n",matriz_confucion)
            
            print("Reporte de clasificacion:\n",reporte_clasificacion, "\n")
            print("Matriz de confucion:\n",matriz_confucion)
   
            
            print("MAE:\n",mae, "\n")
            print("RMSE:\n",mae_sqrt, "\n")
            print("¿En qué porcentaje nos estamos equivocando respecto a la media?\n",
                  mean_desv,
                  "\n")
            print("¿En qué porcentaje nos estamos equivocando respecto a la mediana?\n",
                  median_desv)

            
            # Visualizar nuestra predicción
            plt.scatter(self._data[target], self._predictions)
            plt.xlabel("Valor Real")
            plt.ylabel("Predicción")

            # Predicción perfecta
            plt.plot(self._data[target], self._data[target],'r')

        
        return self
    

        
        
    
class Regression_Model(Modelo_ANN):
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

        if f"Prop_{target}" in inputs.columns:
            inputs = inputs.drop(f"Prop_{target}", axis=1)

        inputs = self._scaler.transform(inputs)
        
        resultado = self.model.predict(inputs)
        
        self._predictions = pd.DataFrame(resultado)
        
        self._data[f"Prop_{target}"] = self._predictions
        
        if eval:
            
            mae = mean_absolute_error(
                self._data[target],
                self._predictions)
            
            mae_sqrt = np.sqrt( 
                            mean_squared_error(
                                self._data[target],
                                self._predictions
                                )
                               )
            

            
            if self._data[target].median() != 0:
                median_desv = mean_absolute_error(self._data[target], self._predictions)/self._data[target].median()
                
            if self._data[target].median() == 0:
                median_desv = "Divicion entre 0"
            
            
            if self._data[target].mean() != 0:
                mean_desv = mean_absolute_error(self._data[target], self._predictions)/self._data[target].mean()
                
            if self._data[target].mean() == 0:
                mean_desv = "Divicion entre 0"  
                
                
            reporte_clasificacion = classification_report(
                self._data[target],
                (self._predictions > 0.8).astype("int32")
                )
            
            matriz_confucion = confusion_matrix(
                self._data[target],
                (self._predictions > 0.8).astype("int32"))
            
            matriz_confucion = pd.DataFrame(
                matriz_confucion, 
                columns=['No abandona(predict) (0)', 'Abandona(predict) (1)'],
                index=['No abandona(real) (0)', 'Abandona(real) (1)']
            )
            
            print("Reporte de clasificacion:\n",reporte_clasificacion, "\n")
            print("Matriz de confucion:\n",matriz_confucion)
   
            
            print("MAE:\n",mae, "\n")
            print("RMSE:\n",mae_sqrt, "\n")
            print("¿En qué porcentaje nos estamos equivocando respecto a la media?\n",
                  mean_desv,
                  "\n")
            print("¿En qué porcentaje nos estamos equivocando respecto a la mediana?\n",
                  median_desv,
                  '\n')



            preds_binarias = (self._predictions > 0.8).astype("int32").to_numpy().flatten()
            
            etiquetas_reales = self._data[target].astype("int32").to_numpy().flatten()
            
            valores_unicos, conteo_real = np.unique(etiquetas_reales, return_counts=True)
            _, conteo_pred = np.unique(preds_binarias, return_counts=True)

            # Asegurar balance de posiciones en el eje X para las dos barras juntas
            posiciones = np.arange(len(valores_unicos))
            ancho_barra = 0.35

            # Dibujar las barras una al lado de la otra
            plt.bar(posiciones - ancho_barra/2, conteo_real, width=ancho_barra, label='Reales', color='royalblue')
            plt.bar(posiciones + ancho_barra/2, conteo_pred, width=ancho_barra, label='Predichos', color='darkorange')

            # Detalles de diseño del gráfico
            plt.xlabel('Clases')
            plt.ylabel('Cantidad de Clientes')
            plt.title('Comparativa de Clases: Reales vs Predichos')
            plt.xticks(posiciones, ['No abandona (0)', 'Abandona (1)'])
            plt.legend()
            plt.show()
            
        
        return self