# Meeting Summarizer

## 1. Overview
Meeting Summarizer turns uploaded meeting audio into a complete transcript and a structured, action-oriented meeting record. It uses Gemini for both audio transcription and transcript analysis; the API key stays on the backend.

## 2. Problem Statement
Long recordings are difficult to review and easy to lose follow-up details in. This application surfaces the summary, discussion points, finalized decisions, supported action items, explicit owners and deadlines, risks, and follow-ups in one readable view.

## 3. Features
- WAV, MP3, M4A, MP4, WebM, and OGG recording validation with a 100 MB default limit.
- Gemini audio transcription and structured Gemini JSON summarization.
- Full transcript plus decisions, action items, risks, and follow-ups.
- Explicit-only owner and deadline extraction with Pydantic validation.
- Local text/JSON result storage under `data/`.
- Responsive browser frontend with clear processing and error states.

## 4. Architecture
```text
User -> Static Frontend -> FastAPI
                          -> Meeting Service
                             -> Gemini audio transcription -> Transcript
                             -> Gemini structured summary -> Pydantic validation
                          -> Local transcript/text and summary/JSON storage
```

## 5. Workflow
Audio upload -> input validation -> Gemini transcription -> usable transcript -> Gemini structured summary -> validation -> local storage -> UI.

## 6. Technology Stack
Python 3.10+, FastAPI, Uvicorn, Pydantic v2, `google-genai`, python-dotenv, vanilla HTML/CSS/JavaScript, and pytest.

## 7. Project Structure
- `app/config.py`: environment-backed settings.
- `app/routes/`: health and processing endpoints.
- `app/services/`: Gemini, transcription, meeting orchestration, and storage.
- `app/models/`: response and summary schemas.
- `app/prompts/`: transcription and anti-hallucination summary prompts.
- `frontend/`: static demo interface.
- `tests/`: mocked service and API tests.
- `data/`: generated runtime results.

## 8. Setup (Windows)
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
```
If PowerShell blocks activation, run the project interpreter directly: `& .\.venv\Scripts\python.exe -m uvicorn app.main:app --reload`.

## 9. Environment Variables
Put these in the local, uncommitted `.env` file:
```text
GEMINI_API_KEY=your-key-created-in-Google-AI-Studio
GEMINI_MODEL=gemini-2.5-flash
MAX_UPLOAD_SIZE_MB=100
```
Create the key yourself in Google AI Studio. Never put it in frontend code, source control, or chat. `.env.example` contains placeholders only.

## 10. Running the Application
```powershell
.\.venv\Scripts\Activate.ps1
python -m uvicorn app.main:app --reload
```
Open <http://127.0.0.1:8000>.

## 11. API Endpoints
- `GET /health`: returns `{"status":"ok"}`.
- `POST /api/meetings/process`: multipart form upload with field `file`; returns `meeting_id`, filename, transcript, and validated summary.

## 12. LLM Prompt Strategy
The dedicated prompt frames Gemini as an expert meeting analyst and requires JSON matching the Pydantic schema. It separates finalized decisions from proposals, requires evidence for action items, and uses null or empty arrays when owners, deadlines, decisions, risks, or follow-ups are not supported. The transcript is the only source of truth.

## 13. ASR / Transcription
`TranscriptionService` hides the provider boundary. The current implementation uploads the validated audio or MP4 recording through the official `google-genai` SDK and asks Gemini to return the complete transcript. A provider failure stops the pipeline; no summary is generated without a usable transcript.

## 14. Testing
External calls are mocked, so tests do not consume Gemini quota:
```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

## 15. Example Workflow
Create `.env`, start the server, open the browser, choose a meeting recording, click **Process meeting**, then review the transcript, summary, decisions, action table, risks, and follow-ups.

## 16. Design Decisions
The app uses one FastAPI process and local storage to keep the assignment easy to run and inspect. Gemini model configuration is centralized, provider-specific code is isolated, and structured output is validated before storage or display.

## 17. Limitations
Transcription and summary quality depend on the audio quality, language, file duration, Gemini model, and API quota. Local storage is not multi-user or durable across machines. Real Gemini processing requires a user-provided API key.

## 18. Future Improvements
Add persistent database storage, speaker diarization, timestamps, history, downloadable exports, and background jobs for long recordings.

## 19. Demo Instructions
Start Uvicorn, open the local URL, upload a short recording, and show the generated transcript followed by the executive summary and action-item table. Explain that the browser calls only FastAPI and the Gemini secret is read from backend `.env` configuration.
