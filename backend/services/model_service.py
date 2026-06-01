from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import httpx
from PIL import Image

from backend.core.config import get_settings


@dataclass
class ScreeningPrediction:
    probability: float | None
    confidence: float | None
    risk_level: str
    recommendation: str
    model_name: str
    model_status: str
    threshold_uncertain: float
    threshold_high: float


class ModelNotConfiguredError(RuntimeError):
    pass


class GlaucomaModelService:
    """Stable model adapter used by the FastAPI screening endpoint.

    Keep Streamlit and the rest of the backend unchanged. After you finish model
    training, integrate your Vision Transformer, ResNet, EfficientNet, or any
    other model here.
    """

    def __init__(self) -> None:
        self.settings = get_settings()
        self._local_model: Any | None = None

    def predict(self, image_path: str | Path) -> ScreeningPrediction:
        backend = self.settings.model_backend.lower().strip()
        if backend == "external_api":
            return self._predict_external_api(Path(image_path))
        if backend == "local_torch":
            return self._predict_local_torch(Path(image_path))
        return ScreeningPrediction(
            probability=None,
            confidence=None,
            risk_level="Model Not Configured",
            recommendation="The image was uploaded successfully. Configure the trained glaucoma screening model to enable automated risk analysis.",
            model_name="not-configured",
            model_status="not_configured",
            threshold_uncertain=self.settings.model_threshold_uncertain,
            threshold_high=self.settings.model_threshold_high,
        )

    def _risk_from_probability(self, probability: float) -> tuple[str, str]:
        if probability >= self.settings.model_threshold_high:
            return (
                "High Risk",
                "High glaucoma-risk indicators were detected. Booking an ophthalmology appointment is recommended.",
            )
        if probability >= self.settings.model_threshold_uncertain:
            return (
                "Uncertain",
                "The result is borderline. Ophthalmology review is recommended, especially if symptoms or risk factors are present.",
            )
        return (
            "Low Risk",
            "No high-risk glaucoma indicators were detected by the configured model. Routine eye care remains recommended when symptoms or risk factors exist.",
        )

    def _predict_external_api(self, image_path: Path) -> ScreeningPrediction:
        headers = {}
        if self.settings.model_api_key:
            headers["Authorization"] = f"Bearer {self.settings.model_api_key}"
        with image_path.open("rb") as fh:
            files = {"file": (image_path.name, fh, "application/octet-stream")}
            response = httpx.post(self.settings.model_api_url, headers=headers, files=files, timeout=60)
        response.raise_for_status()
        data = response.json()
        probability = float(data.get("probability", data.get("confidence", 0.0)))
        risk_level, recommendation = self._risk_from_probability(probability)
        return ScreeningPrediction(
            probability=probability,
            confidence=float(data.get("confidence", probability)),
            risk_level=str(data.get("label") or risk_level),
            recommendation=str(data.get("recommendation") or recommendation),
            model_name=str(data.get("model_name") or "external-glaucoma-model"),
            model_status="configured",
            threshold_uncertain=self.settings.model_threshold_uncertain,
            threshold_high=self.settings.model_threshold_high,
        )

    def _predict_local_torch(self, image_path: Path) -> ScreeningPrediction:
        # ------------------------------------------------------------------
        # LOCAL MODEL INTEGRATION POINT
        # ------------------------------------------------------------------
        # 1. Place your checkpoint in models/glaucoma_model.pt or set MODEL_PATH.
        # 2. Implement _build_local_torch_model() with your architecture.
        # 3. Implement _preprocess_for_local_model() with the same transforms
        #    used in training.
        # 4. Return the positive-class probability for glaucoma.
        # ------------------------------------------------------------------
        try:
            import torch
        except Exception as exc:
            raise ModelNotConfiguredError("PyTorch is required for local_torch mode.") from exc

        if not self.settings.model_file_path.exists():
            raise ModelNotConfiguredError(f"Model file was not found: {self.settings.model_file_path}")

        if self._local_model is None:
            self._local_model = self._build_local_torch_model(torch)
            checkpoint = torch.load(self.settings.model_file_path, map_location=self.settings.model_device)
            if isinstance(checkpoint, dict) and "state_dict" in checkpoint:
                checkpoint = checkpoint["state_dict"]
            self._local_model.load_state_dict(checkpoint)
            self._local_model.to(self.settings.model_device)
            self._local_model.eval()

        tensor = self._preprocess_for_local_model(torch, image_path).to(self.settings.model_device)
        with torch.no_grad():
            logits = self._local_model(tensor)
            if logits.ndim == 2 and logits.shape[1] == 2:
                probability = float(torch.softmax(logits, dim=1)[0, 1].item())
            else:
                probability = float(torch.sigmoid(logits.reshape(-1)[0]).item())
        risk_level, recommendation = self._risk_from_probability(probability)
        return ScreeningPrediction(
            probability=probability,
            confidence=probability,
            risk_level=risk_level,
            recommendation=recommendation,
            model_name=self.settings.model_file_path.name,
            model_status="configured",
            threshold_uncertain=self.settings.model_threshold_uncertain,
            threshold_high=self.settings.model_threshold_high,
        )

    def _build_local_torch_model(self, torch):
        raise ModelNotConfiguredError(
            "Implement _build_local_torch_model() in backend/services/model_service.py to load your trained architecture."
        )

    def _preprocess_for_local_model(self, torch, image_path: Path):
        # Replace this with the exact validation/test preprocessing from your notebook.
        # A minimal placeholder is left here only to show the expected return type.
        from torchvision import transforms

        image = Image.open(image_path).convert("RGB")
        transform = transforms.Compose([
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
        ])
        return transform(image).unsqueeze(0)
