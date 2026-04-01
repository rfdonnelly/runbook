from dataclasses import dataclass
from enum import Enum
from typing import TextIO


class ChunkType(Enum):
    Markup = 1
    CommandBlock = 2


@dataclass
class Chunk:
    type: ChunkType
    lines: list[str]


class State(Enum):
    Markup = 1
    CommandBlockHeader = 2
    CommandBlockBody = 3


class AdocReader:
    reader: TextIO
    state: State
    previous_line: str | None
    eof: bool

    def __init__(self, reader: TextIO):
        self.reader = reader
        self.state = State.Markup
        self.previous_line = None
        self.eof = False

    def next_chunk(self) -> Chunk | None:
        if self.eof:
            return None

        if self.previous_line:
            lines = [self.previous_line]
            self.previous_line = None
        else:
            lines = []

        while True:
            line = self.reader.readline()
            if self.is_eof(line):
                if not lines:
                    return None
                else:
                    self.eof = True
                    return Chunk(type=ChunkType.Markup, lines=lines)

            match self.state:
                case State.Markup:
                    if self.is_eof(line):
                        self.eof = True
                        return Chunk(type=ChunkType.Markup, lines=lines)
                    elif self.is_start_of_command_block_header(line):
                        lines.append(line)
                        self.state = State.CommandBlockHeader
                    else:
                        lines.append(line)
                case State.CommandBlockHeader:
                    lines.append(line)
                    if self.is_eof(line):
                        raise ApplicationError(
                            "Reached EOF while parsing a command block header"
                        )
                    elif self.is_command_block_body_delimiter(line):
                        self.state = State.CommandBlockBody
                        return Chunk(type=ChunkType.Markup, lines=lines)
                case State.CommandBlockBody:
                    if self.is_eof(line):
                        raise ApplicationError(
                            "Reached EOF while parsing a command block body"
                        )
                    elif self.is_command_block_body_delimiter(line):
                        self.state = State.Markup
                        self.previous_line = line
                        return Chunk(type=ChunkType.CommandBlock, lines=lines)
                    else:
                        lines.append(line)

    @staticmethod
    def is_eof(line: str) -> bool:
        return line == ""

    @staticmethod
    def is_start_of_command_block_header(line: str) -> bool:
        return line.startswith("[source,sh]")

    @staticmethod
    def is_command_block_body_delimiter(line: str) -> bool:
        return line.startswith("----")
