from app.parsers.chatgpt_parser import ChatGPTParser
from app.parsers.chatgpt_share_parser import ChatGPTShareParser
from app.parsers.markdown_parser import MarkdownParser
from app.parsers.pdf_parser import PDFParser
from app.parsers.text_parser import TxtParser
from app.parsers.base import BaseParser

PARSER_MAP: dict[str, type[BaseParser]] = {
    "chatgpt": ChatGPTParser,
    "chatgpt_share": ChatGPTShareParser,
    "markdown": MarkdownParser,
    "txt": TxtParser,
    "pdf": PDFParser,
}

EXT_MAP: dict[str, str] = {
    ".json": "chatgpt",
    ".md": "markdown",
    ".markdown": "markdown",
    ".txt": "txt",
    ".pdf": "pdf",
}

SHARE_PARSER_MAP: dict[str, type[ChatGPTShareParser]] = {
    "chatgpt_share": ChatGPTShareParser,
}


def get_parser(source_type: str) -> BaseParser:
    cls = PARSER_MAP.get(source_type)
    if not cls:
        raise ValueError(f"No parser for source_type: {source_type!r}")
    return cls()


def detect_source_type(filename: str) -> str:
    if "." not in filename:
        return "txt"
    ext = "." + filename.rsplit(".", 1)[-1].lower()
    return EXT_MAP.get(ext, "txt")


def get_share_parser(source_type: str) -> ChatGPTShareParser | None:
    cls = SHARE_PARSER_MAP.get(source_type)
    return cls() if cls else None