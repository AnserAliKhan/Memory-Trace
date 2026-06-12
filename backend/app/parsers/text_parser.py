from pathlib import Path
class TextParser:
    def parse(self,file_path:str):
        return Path(file_path).read_text(encoding='utf-8')
