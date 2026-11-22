from pydantic import BaseModel, Field


class RunEventSignal(BaseModel):
    event: int = Field(
        ...,
        description="The event that was triggered. Thhis shoudl be the event id.",
    )
