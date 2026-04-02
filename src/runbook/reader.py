from enum import Enum
import logging
from typing import TextIO


from runbook.datamodel import Chunk, Markup, CodeBlock


logger = logging.getLogger(__name__)


class State(Enum):
    Markup = 1
    CommandBlockHeader = 2
    CommandBlockBody = 3


class AsciidocReader:
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
                    self.strip_blank_lines(lines)
                    return Markup(lines)

            match self.state:
                case State.Markup:
                    if self.is_eof(line):
                        self.eof = True
                        self.strip_blank_lines(lines)
                        return Markup(lines)
                    elif self.is_start_of_code_block_header(line):
                        self.previous_line = line
                        self.state = State.CommandBlockHeader
                        self.strip_blank_lines(lines)
                        return Markup(lines)
                    else:
                        lines.append(line)
                case State.CommandBlockHeader:
                    lines.append(line)
                    if self.is_eof(line):
                        logger.warning(
                            "Reached EOF while parsing a command block header"
                        )
                        self.strip_blank_lines(lines)
                        return Markup(lines)
                    elif self.is_code_block_body_delimiter(line):
                        self.state = State.CommandBlockBody
                case State.CommandBlockBody:
                    if self.is_eof(line):
                        logger.warning("Reached EOF while parsing a command block body")
                        self.strip_blank_lines(lines)
                        return Markup(lines)
                    elif self.is_code_block_body_delimiter(line):
                        self.state = State.Markup
                        lines.append(line)
                        header_end_index = lines.index("----\n")
                        type = lines[0].removeprefix("[source,").removesuffix("]\n")
                        self.strip_blank_lines(lines)
                        return CodeBlock(
                            type=type,
                            lines=lines,
                            body=lines[header_end_index + 1 : -1],
                        )
                    else:
                        lines.append(line)

    @staticmethod
    def strip_blank_lines(lines: list[str]):
        while lines and lines[0] == "\n":
            lines.pop(0)

        while lines and lines[-1] == "\n":
            lines.pop()


    @staticmethod
    def is_eof(line: str) -> bool:
        return line == ""

    @staticmethod
    def is_start_of_code_block_header(line: str) -> bool:
        return line.startswith("[source,sh]") or line.startswith("[source,console]")

    @staticmethod
    def is_code_block_body_delimiter(line: str) -> bool:
        return line.startswith("----")
