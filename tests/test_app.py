import json

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.models.schemas import ActionItem, MeetingSummary
from app.prompts.summarization_prompt import build_summary_prompt
from app.routes import meeting_routes
from app.services.gemini_service import GeminiService, GeminiServiceError, parse_summary_response
from app.services.meeting_service import MeetingService
from app.services.storage_service import StorageService


def test_health_endpoint():
    with TestClient(app) as client:
        response = client.get('/health')
    assert response.status_code == 200
    assert response.json() == {'status': 'ok'}


def test_models_validate_core_fields():
    summary = MeetingSummary(executive_summary='Ship the release.', action_items=[ActionItem(task='Publish notes')])
    assert summary.action_items[0].owner is None
    assert summary.decisions == []


def test_summary_prompt_formats_json_schema_and_transcript():
    prompt = build_summary_prompt('Alex will publish the notes.')
    assert '"executive_summary"' in prompt
    assert 'Alex will publish the notes.' in prompt


def test_mp4_upload_is_supported():
    extension = MeetingService.validate_upload(b"video bytes", "video/mp4", 1000)
    assert extension == ".mp4"


def test_invalid_upload_is_rejected(monkeypatch):
    with TestClient(app) as client:
        response = client.post('/api/meetings/process', files={'file': ('notes.txt', b'hello', 'text/plain')})
    assert response.status_code == 400
    assert 'Unsupported recording type' in response.json()['detail']


def test_missing_gemini_configuration():
    with pytest.raises(GeminiServiceError, match='GEMINI_API_KEY'):
        GeminiService('', 'test-model')


def test_gemini_failure_handling():
    class BrokenClient:
        class files:
            @staticmethod
            def upload(**kwargs):
                raise RuntimeError('provider down')
    service = GeminiService('configured-for-test', 'test-model', client=BrokenClient())
    with pytest.raises(GeminiServiceError, match='provider request failed'):
        service.transcribe('audio.wav', 'audio/wav')


def test_malformed_gemini_response():
    class MalformedClient:
        class models:
            @staticmethod
            def generate_content(**kwargs):
                return type('Response', (), {'text': '{not json'})()
    service = GeminiService('configured-for-test', 'test-model', client=MalformedClient())
    with pytest.raises(GeminiServiceError, match='invalid response'):
        service.summarize('The meeting transcript.')


def test_summary_response_accepts_fenced_json():
    response = type('Response', (), {'text': '```json\n{"executive_summary":"Done"}\n```'})()
    assert parse_summary_response(response).executive_summary == 'Done'


def test_successful_mocked_pipeline(tmp_path):
    class FakeGemini:
        def transcribe(self, audio_path, mime_type):
            return 'Speaker 1: Alex will publish the notes by Friday.'

        def summarize(self, transcript):
            return MeetingSummary(
                executive_summary='The team agreed to publish meeting notes.',
                key_points=['Notes need to be published.'],
                decisions=['The notes will be published.'],
                action_items=[ActionItem(task='Publish the meeting notes', owner='Alex', deadline='Friday')],
            )
    service = MeetingService(StorageService(tmp_path), FakeGemini())
    result = service.process('..\\meeting.mp3', b'audio bytes', 'audio/mpeg', 1000)
    assert result.filename == 'meeting.mp3'
    assert result.summary.action_items[0].owner == 'Alex'
    assert (tmp_path / 'summaries' / f'{result.meeting_id}.json').exists()


def test_api_integration_with_mocked_pipeline(monkeypatch):
    class FakeService:
        def process(self, filename, content, mime_type, max_bytes):
            return {'meeting_id': 'abc', 'filename': filename, 'transcript': 'Transcript', 'summary': {
                'executive_summary': 'Summary', 'key_points': [], 'decisions': [], 'action_items': [], 'risks': [], 'follow_ups': []
            }}
    monkeypatch.setattr(meeting_routes, 'build_meeting_service', lambda: FakeService())
    with TestClient(app) as client:
        response = client.post('/api/meetings/process', files={'file': ('meeting.wav', b'audio', 'audio/wav')})
    assert response.status_code == 200
    assert response.json()['transcript'] == 'Transcript'
