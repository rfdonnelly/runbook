from dataclasses import dataclass


class Chunk:
    pass


@dataclass
class Markup(Chunk):
    lines: list[str]


@dataclass
class CodeBlock(Chunk):
    type: str
    lines: list[str]
    body: list[str]
