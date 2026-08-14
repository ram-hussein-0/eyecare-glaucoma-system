from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

os.environ.setdefault("PYTORCH_ENABLE_MPS_FALLBACK", "1")

import cv2
import httpx
import numpy as np
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


def _crop_fundus_fov(
    image_rgb: np.ndarray,
    margin_ratio: float = 0.02,
) -> np.ndarray:
    gray = cv2.cvtColor(image_rgb, cv2.COLOR_RGB2GRAY)
    gray = cv2.GaussianBlur(gray, (5, 5), 0)

    non_black = gray[gray > 0]
    if non_black.size == 0:
        return image_rgb

    threshold = max(5, int(np.percentile(non_black, 2)))
    mask = (gray > threshold).astype(np.uint8) * 255
    kernel = np.ones((7, 7), np.uint8)

    mask = cv2.morphologyEx(
        mask,
        cv2.MORPH_CLOSE,
        kernel,
        iterations=2,
    )
    mask = cv2.morphologyEx(
        mask,
        cv2.MORPH_OPEN,
        kernel,
        iterations=1,
    )

    contours, _ = cv2.findContours(
        mask,
        cv2.RETR_EXTERNAL,
        cv2.CHAIN_APPROX_SIMPLE,
    )

    if not contours:
        return image_rgb

    contour = max(contours, key=cv2.contourArea)

    if (
        cv2.contourArea(contour)
        < 0.20 * image_rgb.shape[0] * image_rgb.shape[1]
    ):
        return image_rgb

    x, y, width, height = cv2.boundingRect(contour)
    margin = int(max(width, height) * margin_ratio)

    x0 = max(0, x - margin)
    y0 = max(0, y - margin)
    x1 = min(image_rgb.shape[1], x + width + margin)
    y1 = min(image_rgb.shape[0], y + height + margin)

    return image_rgb[y0:y1, x0:x1]


def _apply_clahe_lab(
    image_rgb: np.ndarray,
    clip_limit: float = 2.0,
) -> np.ndarray:
    lab = cv2.cvtColor(image_rgb, cv2.COLOR_RGB2LAB)
    lightness, a_channel, b_channel = cv2.split(lab)

    clahe = cv2.createCLAHE(
        clipLimit=clip_limit,
        tileGridSize=(8, 8),
    )

    enhanced_lightness = clahe.apply(lightness)

    return cv2.cvtColor(
        cv2.merge(
            [
                enhanced_lightness,
                a_channel,
                b_channel,
            ]
        ),
        cv2.COLOR_LAB2RGB,
    )


class _FundusPreprocessor:
    def __call__(self, image: Image.Image) -> Image.Image:
        array = np.asarray(image.convert("RGB"))
        array = _crop_fundus_fov(array)
        array = _apply_clahe_lab(array)
        return Image.fromarray(array)


class GlaucomaModelService:
    def __init__(self) -> None:
        self.settings = get_settings()

        self._local_model: Any | None = None
        self._local_transform: Any | None = None
        self._local_config: dict[str, Any] | None = None
        self._calibration_config: dict[str, Any] | None = None
        self._device: Any | None = None

        self._positive_class = 1
        self._temperature = 1.0

        self._low_threshold = (
            self.settings.model_threshold_uncertain
        )
        self._high_threshold = (
            self.settings.model_threshold_high
        )

        self._local_model_name = "resnet50-glaucoma-v4"

    def predict(
        self,
        image_path: str | Path,
    ) -> ScreeningPrediction:
        backend = self.settings.model_backend.lower().strip()

        if backend == "external_api":
            return self._predict_external_api(Path(image_path))

        if backend == "local_torch":
            return self._predict_local_torch(Path(image_path))

        return ScreeningPrediction(
            probability=None,
            confidence=None,
            risk_level="Model Not Configured",
            recommendation=(
                "The image was uploaded successfully. Configure the trained "
                "glaucoma screening model to enable automated risk analysis."
            ),
            model_name="not-configured",
            model_status="not_configured",
            threshold_uncertain=self.settings.model_threshold_uncertain,
            threshold_high=self.settings.model_threshold_high,
        )

    @staticmethod
    def _risk_from_probability(
        probability: float,
        low_threshold: float,
        high_threshold: float,
    ) -> tuple[str, str]:
        if probability < low_threshold:
            return (
                "Low Risk",
                "No high-risk glaucoma indicators were detected by the "
                "screening model. This is not a diagnosis; seek ophthalmology "
                "review if symptoms or risk factors are present.",
            )

        if probability < high_threshold:
            return (
                "Uncertain",
                "The screening result falls in the uncertainty zone. "
                "Ophthalmology review is recommended.",
            )

        return (
            "High Risk",
            "High glaucoma-risk indicators were detected. Booking an "
            "ophthalmology appointment is recommended.",
        )

    def _predict_external_api(
        self,
        image_path: Path,
    ) -> ScreeningPrediction:
        headers = {}

        if self.settings.model_api_key:
            headers["Authorization"] = (
                f"Bearer {self.settings.model_api_key}"
            )

        with image_path.open("rb") as fh:
            files = {
                "file": (
                    image_path.name,
                    fh,
                    "application/octet-stream",
                )
            }

            response = httpx.post(
                self.settings.model_api_url,
                headers=headers,
                files=files,
                timeout=60,
            )

        response.raise_for_status()
        data = response.json()

        probability = float(
            data.get(
                "probability",
                data.get("confidence", 0.0),
            )
        )

        risk_level, recommendation = self._risk_from_probability(
            probability,
            self.settings.model_threshold_uncertain,
            self.settings.model_threshold_high,
        )

        return ScreeningPrediction(
            probability=probability,
            confidence=float(
                data.get("confidence", probability)
            ),
            risk_level=str(
                data.get("label") or risk_level
            ),
            recommendation=str(
                data.get("recommendation") or recommendation
            ),
            model_name=str(
                data.get("model_name") or "external-glaucoma-model"
            ),
            model_status="configured",
            threshold_uncertain=self.settings.model_threshold_uncertain,
            threshold_high=self.settings.model_threshold_high,
        )

    @staticmethod
    def _load_json(path: Path) -> dict[str, Any]:
        try:
            data = json.loads(
                path.read_text(encoding="utf-8")
            )
        except Exception as exc:
            raise ModelNotConfiguredError(
                f"Could not read model config: {path}"
            ) from exc

        if not isinstance(data, dict):
            raise ModelNotConfiguredError(
                f"Model config must contain a JSON object: {path}"
            )

        return data

    def _resolve_device(self, torch):
        requested = (
            self.settings.model_device or "auto"
        ).strip().lower()

        if requested in {"", "auto"}:
            if (
                hasattr(torch.backends, "mps")
                and torch.backends.mps.is_available()
            ):
                return torch.device("mps")

            if torch.cuda.is_available():
                return torch.device("cuda")

            return torch.device("cpu")

        if requested == "mps":
            if not (
                hasattr(torch.backends, "mps")
                and torch.backends.mps.is_available()
            ):
                raise ModelNotConfiguredError(
                    "MODEL_DEVICE=mps but MPS is not available."
                )

            return torch.device("mps")

        if (
            requested.startswith("cuda")
            and not torch.cuda.is_available()
        ):
            raise ModelNotConfiguredError(
                f"MODEL_DEVICE={requested} but CUDA is not available."
            )

        try:
            return torch.device(requested)
        except Exception as exc:
            raise ModelNotConfiguredError(
                f"Unsupported MODEL_DEVICE value: {requested!r}"
            ) from exc

    def _ensure_local_bundle_loaded(self, torch) -> None:
        if self._local_model is not None:
            return

        try:
            from torch import nn
            from torchvision import models, transforms
        except Exception as exc:
            raise ModelNotConfiguredError(
                "torchvision is required for the deployed ResNet50 model."
            ) from exc

        model_path = self.settings.model_file_path
        config_path = model_path.with_name("screening_config.json")
        calibration_path = model_path.with_name(
            "calibrated_screening_config.json"
        )

        if not model_path.exists():
            raise ModelNotConfiguredError(
                f"Model file was not found: {model_path}"
            )

        if not config_path.exists():
            raise ModelNotConfiguredError(
                "screening_config.json was not found beside the model: "
                f"{config_path}"
            )

        config = self._load_json(config_path)

        if config.get("architecture") != "resnet50":
            raise ModelNotConfiguredError(
                "Expected architecture='resnet50', got "
                f"{config.get('architecture')!r}."
            )

        if config.get("class_names") != [
            "Non-Glaucoma",
            "Glaucoma",
        ]:
            raise ModelNotConfiguredError(
                "Unexpected class_names in screening_config.json: "
                f"{config.get('class_names')!r}"
            )

        positive_class = int(
            config.get("positive_class", 1)
        )

        if positive_class != 1:
            raise ModelNotConfiguredError(
                "Expected glaucoma positive_class=1, got "
                f"{positive_class}."
            )

        preprocess_mode = str(
            config.get("preprocess_mode", "")
        ).strip()

        if preprocess_mode != "crop_clahe":
            raise ModelNotConfiguredError(
                "The deployed scientific bundle requires "
                "preprocess_mode='crop_clahe'; got "
                f"{preprocess_mode!r}."
            )

        try:
            payload = torch.load(
                model_path,
                map_location="cpu",
                weights_only=True,
            )
        except TypeError:
            payload = torch.load(
                model_path,
                map_location="cpu",
            )
        except Exception:
            # This checkpoint is trusted and hash-verified by the installer.
            payload = torch.load(
                model_path,
                map_location="cpu",
                weights_only=False,
            )

        if (
            not isinstance(payload, dict)
            or "state_dict" not in payload
        ):
            raise ModelNotConfiguredError(
                "The ResNet50 checkpoint must be a dict containing "
                "'state_dict'."
            )

        if payload.get("architecture") not in {
            None,
            "resnet50",
        }:
            raise ModelNotConfiguredError(
                "Checkpoint architecture is unexpected: "
                f"{payload.get('architecture')!r}"
            )

        hidden_features = int(
            payload.get(
                "classifier_hidden_features",
                256,
            )
        )

        model = models.resnet50(weights=None)
        input_features = model.fc.in_features

        model.fc = nn.Sequential(
            nn.Dropout(p=0.30),
            nn.Linear(
                input_features,
                hidden_features,
            ),
            nn.ReLU(inplace=True),
            nn.Dropout(p=0.20),
            nn.Linear(hidden_features, 2),
        )

        try:
            model.load_state_dict(
                payload["state_dict"],
                strict=True,
            )
        except Exception as exc:
            raise ModelNotConfiguredError(
                "The checkpoint state_dict does not match the "
                "deployed ResNet50 architecture."
            ) from exc

        image_size = int(
            config.get("image_size", 224)
        )
        mean = [
            float(value)
            for value in config.get(
                "normalization_mean",
                [],
            )
        ]
        std = [
            float(value)
            for value in config.get(
                "normalization_std",
                [],
            )
        ]

        if (
            image_size != 224
            or len(mean) != 3
            or len(std) != 3
        ):
            raise ModelNotConfiguredError(
                "Invalid image_size or normalization settings in "
                "screening_config.json."
            )

        transform = transforms.Compose(
            [
                _FundusPreprocessor(),
                transforms.Resize(
                    (image_size, image_size),
                    antialias=True,
                ),
                transforms.ToTensor(),
                transforms.Normalize(
                    mean=mean,
                    std=std,
                ),
            ]
        )

        calibration = None
        temperature = 1.0
        threshold_source = config

        if calibration_path.exists():
            calibration = self._load_json(
                calibration_path
            )

            method = str(
                calibration.get("method", "")
            ).strip().lower()

            if method != "temperature":
                raise ModelNotConfiguredError(
                    "Unsupported probability calibration method for "
                    f"deployment: {method!r}"
                )

            temperature = float(
                calibration.get(
                    "temperature",
                    0.0,
                )
            )

            if not temperature > 0.0:
                raise ModelNotConfiguredError(
                    "Temperature calibration value must be positive."
                )

            threshold_source = calibration

        try:
            low_threshold = float(
                threshold_source["low_risk_threshold"]
            )
            high_threshold = float(
                threshold_source["high_risk_threshold"]
            )
        except Exception as exc:
            raise ModelNotConfiguredError(
                "Risk thresholds are missing from the active screening "
                "configuration."
            ) from exc

        if not (
            0.0
            <= low_threshold
            < high_threshold
            <= 1.0
        ):
            raise ModelNotConfiguredError(
                "Invalid risk thresholds: "
                f"low={low_threshold}, high={high_threshold}"
            )

        device = self._resolve_device(torch)

        model = model.to(device).eval()

        self._local_model = model
        self._local_transform = transform
        self._local_config = config
        self._calibration_config = calibration
        self._device = device
        self._positive_class = positive_class
        self._temperature = temperature
        self._low_threshold = low_threshold
        self._high_threshold = high_threshold

        base_name = str(
            config.get("model_name")
            or "resnet50-glaucoma-v4"
        )

        suffix = (
            "-temperature-calibrated"
            if calibration is not None
            else ""
        )

        self._local_model_name = (
            f"{base_name}{suffix}"
        )

    def _predict_local_torch(
        self,
        image_path: Path,
    ) -> ScreeningPrediction:
        try:
            import torch
        except Exception as exc:
            raise ModelNotConfiguredError(
                "PyTorch is required for local_torch mode."
            ) from exc

        self._ensure_local_bundle_loaded(torch)

        try:
            with Image.open(image_path) as image:
                tensor = (
                    self._local_transform(
                        image.convert("RGB")
                    )
                    .unsqueeze(0)
                )
        except Exception as exc:
            raise ValueError(
                f"Could not decode fundus image: {image_path.name}"
            ) from exc

        tensor = tensor.to(self._device)

        with torch.inference_mode():
            logits = self._local_model(tensor)

            if (
                logits.ndim != 2
                or tuple(logits.shape) != (1, 2)
            ):
                raise RuntimeError(
                    "Unexpected ResNet50 output shape: "
                    f"{tuple(logits.shape)}; expected (1, 2)."
                )

            calibrated_logits = (
                logits / self._temperature
            )

            probabilities = torch.softmax(
                calibrated_logits,
                dim=1,
            )[0]

            probability = float(
                probabilities[
                    self._positive_class
                ].item()
            )

            confidence = float(
                probabilities.max().item()
            )

        risk_level, recommendation = (
            self._risk_from_probability(
                probability,
                self._low_threshold,
                self._high_threshold,
            )
        )

        return ScreeningPrediction(
            probability=probability,
            confidence=confidence,
            risk_level=risk_level,
            recommendation=recommendation,
            model_name=self._local_model_name,
            model_status="configured",
            threshold_uncertain=self._low_threshold,
            threshold_high=self._high_threshold,
        )
