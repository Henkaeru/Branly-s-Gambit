from pydantic import BaseModel, Field

class AudioConfig(BaseModel):
    enabled: bool = True

    master_volume: float = Field(1.0, ge=0.0, le=1.0)
    sfx_volume: float = Field(1.0, ge=0.0, le=1.0)
    music_volume: float = Field(0.8, ge=0.0, le=1.0)

    preload: bool = True