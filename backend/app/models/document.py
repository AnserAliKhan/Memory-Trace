from pydantic import BaseModel
from datetime import datetime

class Document(BaseModel):
    id:str
    title:str
    source_type:str
    content:str
    file_path:str|None=None
    created_at:datetime
