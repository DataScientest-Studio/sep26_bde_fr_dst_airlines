import os
import logging
from typing import List
import joblib
import pandas as pd
from fastapi import HTTPException, status
from src.api.config import settings
from src.api.schemas import FlightPredictionInput, PredictionOutput

logger = logging.getLogger(__name__)


class MLModelManager:
    def __init__(self) -> None:
        self.model = None

    def load_model(self) -> None:
        """Charge le modèle Scikit-Learn au démarrage de l'API."""
        if os.path.exists(settings.MODEL_PATH):
            self.model = joblib.load(settings.MODEL_PATH)
            logger.info(f"Modèle Scikit-Learn chargé depuis {settings.MODEL_PATH}")
        else:
            logger.warning(f"Fichier modèle introuvable ({settings.MODEL_PATH}).")

    def predict(self, inputs: List[FlightPredictionInput]) -> List[PredictionOutput]:
        if not inputs:
            return []

        df = pd.DataFrame([item.model_dump() for item in inputs])

        if self.model is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Le modèle Scikit-Learn n'est pas chargé (chemin attendu: {settings.MODEL_PATH}).",
            )

        preds = self.model.predict(df)
        probas = self.model.predict_proba(df)[:, 1] if hasattr(self.model, "predict_proba") else None

        results: List[PredictionOutput] = []
        for idx, pred in enumerate(preds):
            delay_val = float(pred)
            prob_val = float(probas[idx]) if probas is not None else None
            results.append(
                PredictionOutput(
                    predicted_delay_minutes=delay_val,
                    is_delayed=(delay_val >= 15.0) if prob_val is None else (prob_val >= 0.5),
                    delay_probability=prob_val,
                )
            )
        return results


ml_manager = MLModelManager()
