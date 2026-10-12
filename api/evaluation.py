# ESTADO_ARCHIVO: EN_MODIFICACION
"""Mismas fórmulas de evaluación que Binary_Model/Regression_Model de src en WSL."""
import numpy as np
from sklearn.metrics import (accuracy_score, average_precision_score, classification_report,
    confusion_matrix, f1_score, mean_absolute_error, mean_squared_error,
    precision_score, recall_score, roc_auc_score)


def metricas(results, truth, conjunto, predictor):
    truth = np.asarray(truth, dtype=int)
    rows, matrices, reports = [], {}, {}
    clients = [{"fila": i + 1, "Real": int(label)} for i, label in enumerate(truth)]
    for slot, predictions in results.items():
        probabilities = np.asarray([p.probabilidad for p in predictions])
        predicted = np.asarray([int(p.abandono == "Yes") for p in predictions])
        # Binary_Model evalúa clases; Regression_Model evalúa su salida continua.
        output = predicted if slot == "modelo_1" else probabilities
        mae = mean_absolute_error(truth, output)
        mean, median = float(truth.mean()), float(np.median(truth))
        rows.append({"Slot": slot, "Modelo": getattr(predictor.config, slot), "Conjunto": conjunto,
            "Salida evaluada": "Clasificación 0/1" if slot == "modelo_1" else "Probabilidad de abandono",
            "N": len(truth), "Umbral": predictor.config.umbral,
            "MAE": mae, "RMSE": float(np.sqrt(mean_squared_error(truth, output))),
            "MAE / media": mae / mean if mean != 0 else None,
            "MAE / mediana": mae / median if median != 0 else None,
            "Accuracy": accuracy_score(truth, predicted),
            "Precision": precision_score(truth, predicted, zero_division=0),
            "Recall": recall_score(truth, predicted, zero_division=0),
            "F1": f1_score(truth, predicted, zero_division=0),
            "ROC AUC": roc_auc_score(truth, probabilities) if len(set(truth)) == 2 else None,
            "Average precision": average_precision_score(truth, probabilities) if len(set(truth)) == 2 else None})
        matrices[slot] = confusion_matrix(truth, predicted, labels=[0, 1]).tolist()
        reports[slot] = classification_report(truth, predicted, labels=[0, 1],
            target_names=["Permanece (0)", "Abandona (1)"], output_dict=True, zero_division=0)
        for row, label, probability in zip(clients, predicted, probabilities):
            row[f"{slot}_clase"] = int(label)
            if slot == "modelo_2":
                row["modelo_2_probabilidad"] = float(probability)
    return {"metricas": rows, "matrices": matrices, "reportes": reports,
            "clientes": clients, "revision": predictor.revision}
