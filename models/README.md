# Deployed glaucoma screening model

The site uses the final ResNet50 glaucoma screening bundle:

- `resnet50_glaucoma_state_dict.pt`
- `screening_config.json`
- `calibrated_screening_config.json`

Runtime pipeline:

`fundus image -> FOV crop -> LAB CLAHE -> resize 224x224 -> ImageNet normalization -> ResNet50 -> temperature calibration -> Low / Uncertain / High Risk`

The ResNet50 classifier head is:

`Dropout(0.30) -> Linear(2048, 256) -> ReLU -> Dropout(0.20) -> Linear(256, 2)`

Positive class:

`1 = Glaucoma`

The active deployment uses the temperature-calibrated probability and the calibrated Low/Uncertain/High thresholds from `calibrated_screening_config.json`.

This output is for preliminary screening and is not a final medical diagnosis.
