from pydantic import BaseModel, Field


class ActionItem(BaseModel):
    task: str = Field(min_length=1)
    owner: str | None = None
    deadline: str | None = None


class MeetingSummary(BaseModel):
    executive_summary: str = Field(min_length=1)
    key_points: list[str] = Field(default_factory=list)
    decisions: list[str] = Field(default_factory=list)
    action_items: list[ActionItem] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)
    follow_ups: list[str] = Field(default_factory=list)


class MeetingResult(BaseModel):
    meeting_id: str
    filename: str
    transcript: str
    summary: MeetingSummary


class HealthResponse(BaseModel):
    status: str
