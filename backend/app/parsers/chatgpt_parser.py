import json
from pathlib import Path
class ChatGPTParser:
    def parse(self,file_path:str):
        return json.loads(Path(file_path).read_text(encoding='utf-8'))
