from dataclasses import dataclass, field


class Chunk:
    pass


@dataclass
class Markup(Chunk):
    lines: list[str]


@dataclass
class CodeBlock(Chunk):
    type: str
    lines: list[str]
    body: list[str] = field(default_factory=list)
    captures: list[str] = field(default_factory=list)
    shell_new: bool = False
    shell_id: str = "default"
