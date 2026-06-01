# OptiCare Glaucoma Screening & Appointment System

A deployable Streamlit + FastAPI system for ophthalmology appointments, preliminary glaucoma screening workflow, patient reports, doctor follow-up, and a RAG-based assistant.

The system is centered on preliminary glaucoma screening from fundus images and medical appointment management. The trained Vision Transformer or any other glaucoma model is intentionally isolated behind a model adapter so you can integrate your final model without changing the Streamlit interface, database, appointment logic, reports, or assistant pages.

## Main features

- Patient, doctor, and admin roles.
- Doctor registration with admin approval before appearing to patients.
- Doctor availability management and slot-based appointment booking.
- Patient appointment tracking and cancellation.
- Fundus image screening workflow with a dedicated model integration layer.
- Rule-based eye symptom triage that recommends whether the patient should visit an ophthalmologist.
- Structured patient reports in HTML and PDF.
- RAG assistant for system guidance, glaucoma information, report explanation, and booking support.
- FastAPI backend and Streamlit frontend.
- SQLite by default, with a repository/service structure that can be migrated to PostgreSQL later.

## Project structure

```text
eyecare_glaucoma_system/
  backend/                 FastAPI application, database, services
  frontend/                Streamlit application and pages
  data/                    SQLite DB, uploads, reports, RAG documents
  models/                  Place your trained glaucoma model here
  scripts/                 Helper scripts
  requirements.txt
  .env.example
```

## Quick start

### 1. Create and activate a virtual environment

```bash
cd eyecare_glaucoma_system
python -m venv .venv
source .venv/bin/activate        # macOS/Linux
# .venv\Scripts\activate         # Windows
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Create configuration

```bash
cp .env.example .env
```

The application also works with default values if `.env` is not created, but using `.env` is recommended.

### 4. Initialize the database

```bash
python -m backend.db.seed
```

This creates tables and inserts default accounts, sample doctors, availability, and RAG documents.

### 5. Start the FastAPI backend

```bash
uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
```

### 6. Start the Streamlit frontend in another terminal

```bash
PYTHONPATH=. streamlit run frontend/Home.py
```

## Default accounts

Use these accounts after running the seed command:

| Role | Email | Password |
|---|---|---|
| Admin | admin@opticcare.com | Admin@12345 |
| Patient | patient@example.com | Patient@12345 |
| Approved Doctor | doctor@example.com | Doctor@12345 |
| Pending Doctor | pending.doctor@example.com | Doctor@12345 |

Change these credentials before deployment.

## Model integration

The interface is ready for your final glaucoma model. The rest of the project calls one stable API endpoint:

```text
POST /screening/analyze
```

Internally, this endpoint calls:

```python
backend/services/model_service.py
GlaucomaModelService.predict(image_path)
```

You have two integration options.

### Option A: External model API

Use this if your trained model is served separately, for example from another FastAPI app.

Set in `.env`:

```env
MODEL_BACKEND=external_api
MODEL_API_URL=http://127.0.0.1:9000/predict
MODEL_API_KEY=optional-key
```

Your model API should accept a multipart image upload and return JSON like:

```json
{
  "probability": 0.84,
  "label": "High Risk",
  "confidence": 0.84,
  "model_name": "vit-glaucoma-v1"
}
```

### Option B: Local PyTorch checkpoint

Set in `.env`:

```env
MODEL_BACKEND=local_torch
MODEL_PATH=models/glaucoma_model.pt
MODEL_DEVICE=cpu
MODEL_THRESHOLD_UNCERTAIN=0.20
MODEL_THRESHOLD_HIGH=0.60
```

Then edit only the clearly marked section in:

```text
backend/services/model_service.py
```

Specifically implement:

```python
_build_local_torch_model()
_preprocess_for_local_model()
```

The Streamlit frontend, database, reports, appointment module, and API endpoints do not need to change.

## RAG assistant integration

RAG documents are stored in:

```text
data/rag_docs/
```

The admin panel can also create knowledge base documents stored in the database. If no LLM provider is configured, the assistant returns grounded retrieval-based answers. To enable an OpenAI-compatible provider, set:

```env
LLM_PROVIDER=openai_compatible
LLM_BASE_URL=https://api.openai.com/v1
LLM_API_KEY=your-key
LLM_MODEL=gpt-4o-mini
```

The assistant uses retrieval first, then passes only the retrieved context to the LLM.

## Notes for deployment

- Replace the default `SECRET_KEY`.
- Use PostgreSQL or a managed database for multi-user production deployment.
- Put uploaded images and reports in protected storage.
- Configure HTTPS.
- Configure a real model backend before enabling automated screening in a live clinical workflow.
- Keep the screening language preliminary and supportive; final diagnosis belongs to an ophthalmologist.


## Enabling the AI Assistant with Groq or any OpenAI-compatible provider

Create a `.env` file in the project root. You can copy `.env.example` first:

```bash
cp .env.example .env
```

Then set the provider values, for example:

```env
LLM_PROVIDER=groq
LLM_BASE_URL=https://api.groq.com/openai/v1
LLM_API_KEY=gsk_your_key_here
LLM_MODEL=put_the_model_id_from_your_groq_dashboard_here
```

Restart the FastAPI backend after editing `.env`. The Streamlit frontend can stay open, but restarting it is also safe.
