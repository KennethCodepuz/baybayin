from typing import Literal

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class Canvas(BaseModel):
    model_config = ConfigDict(extra='forbid')
    width: int = Field(gt=0)
    height: int = Field(gt=0)


class Event(BaseModel):
    model_config = ConfigDict(extra='forbid', allow_inf_nan=False)
    type: Literal['down', 'move', 'up']
    x: float
    y: float
    timestamp: float = Field(ge=0)
    pointerType: str = Field(min_length=1, max_length=20)


class Sample(BaseModel):
    model_config = ConfigDict(extra='forbid')
    version: Literal[1]
    createdAt: str = Field(min_length=1, max_length=40)
    target: str = Field(min_length=1, max_length=100)
    canvas: Canvas
    image: str = Field(pattern=r'^data:image/png;base64,[A-Za-z0-9+/]+={0,2}$', max_length=10_000_000)
    events: list[Event] = Field(min_length=2, max_length=100_000)

    @field_validator('target')
    @classmethod
    def target_must_not_be_blank(cls, value):
        if not value.strip():
            raise ValueError('Target character must not be blank')
        return value

    @model_validator(mode='after')
    def complete_strokes(self):
        active = False
        last_timestamp = -1
        for event in self.events:
            if event.timestamp < last_timestamp:
                raise ValueError('Event timestamps must be ordered')
            last_timestamp = event.timestamp
            if event.type == 'down':
                if active:
                    raise ValueError('A stroke cannot start before the previous stroke ends')
                active = True
            elif not active:
                raise ValueError('A stroke must start before move or up')
            elif event.type == 'up':
                active = False
        if active:
            raise ValueError('The last stroke is incomplete')
        return self


app = FastAPI(title='Baybayin capture API')
app.add_middleware(
    CORSMiddleware,
    allow_origins=['http://localhost:3000', 'http://127.0.0.1:3000'],
    allow_methods=['POST'],
    allow_headers=['Content-Type'],
)


@app.post('/api/samples/check')
def check_sample(sample: Sample):
    # Checks capture structure only; this does not validate Baybayin writing.
    return {'sample': sample}
