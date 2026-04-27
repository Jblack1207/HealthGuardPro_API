from pydantic import BaseModel


class FaceImageResponse(BaseModel):
    filename: str
    url: str
