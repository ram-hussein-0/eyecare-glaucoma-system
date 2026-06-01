# Model integration folder

Place your trained glaucoma screening model checkpoint here, for example:

```text
models/glaucoma_model.pt
```

Then configure `.env`:

```env
MODEL_BACKEND=local_torch
MODEL_PATH=models/glaucoma_model.pt
MODEL_DEVICE=cpu
```

Implement the marked local PyTorch sections in:

```text
backend/services/model_service.py
```

No Streamlit page needs to change.
