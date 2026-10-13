import sys
import os

sys.path.append(os.path.abspath(os.path.join('..')))

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from scipy.stats import gaussian_kde

class Graficos:
    def __init__(self):
        pass
    
    
    
    
    def plot_boxplot_histogram(self, df, column):
        x = df[column].dropna()
        fig, (ax_box, ax_hist) = plt.subplots(2, 1, sharex=True, figsize=(10, 6),
                                            gridspec_kw={"height_ratios": [1, 4]})
        
        plt.subplot(2, 1, 1).set_title(f"Distribución de la variable '{column}'", fontsize=14, fontweight='bold')
        
        ax_box.boxplot(x, widths=0.6, orientation="horizontal")
        ax_box.set_yticks([])

        ax_hist.hist(x, density=True, alpha=0.6, edgecolor="white")
        xs = np.linspace(x.min(), x.max(), 300)
        ax_hist.plot(xs, gaussian_kde(x)(xs), color="darkblue", lw=2, label="Densidad Estimada por núcleo (KDE)")
        ax_hist.legend()
        plt.show()
        
        
        return self
        
        
        
        
    def plot_bar(self, df, columna, color = ['blue', 'red']):
        barras = tuple(str(unico) for unico in list(df[columna].unique()))
        print(barras)
        alto = []
        for barra in tuple(unico for unico in list(df[columna].unique())):
            alto.append(df.iloc[:, -1].value_counts().get(barra, 0))
        fig, ax = plt.subplots(nrows=1, ncols=1, figsize = (10,5), dpi = 100) #Densidad de pixeles es dpi
        bars = ax.bar(barras, alto, color=color, edgecolor='black', alpha=0.7)
        ax.bar_label(bars, padding=3, fontsize=11, fontweight='bold')
        plt.title(f"Distribución de la variable '{columna}'", fontsize=14, fontweight='bold')
        plt.xlabel(columna)
        plt.ylabel("Frecuencia")
        plt.ylim(0, max(alto) * 1.1) # Para aumentar el limite superior del eje y y que no se corte la barra más alta
        plt.show()
        
        return self