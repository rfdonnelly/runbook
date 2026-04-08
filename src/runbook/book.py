from typing import Iterable

from runbook.datamodel import Chunk, Markup, CodeBlock


class IterError(Exception):
    pass


class Book:
    chunks: list[Chunk]
    index: int

    def __init__(self, chunks: Iterable[Chunk]) -> None:
        self.chunks = list(chunks)
        self.index = 0

    def first_chunk(self) -> Chunk:
        self.index = 0
        return self.chunks[self.index]

    def next_chunk(self) -> Chunk:
        if not self.next_chunk_exists():
            raise IterError()

        self.index += 1
        return self.chunks[self.index]

    def prev_chunk(self) -> Chunk:
        if not self.prev_chunk_exists():
            raise IterError()

        self.index -= 1
        return self.chunks[self.index]

    def prev_chunk_exists(self) -> bool:
        return self.index > 0

    def next_chunk_exists(self) -> bool:
        return self.index <= len(self.chunks) - 2

    def prev_command_block_exists(self) -> bool:
        if self.index <= 0:
            return False

        return any((self.is_command_block(index) for index in range(self.index)))

    def prev_command_block(self) -> Chunk:
        if not self.prev_chunk_exists():
            raise IterError()

        self.index -= 1
        while self.index > 0 and not self.is_command_block(self.index):
            self.index -= 1

        # Go back to markup if present since it may
        # contain info about the command block
        if self.index > 0 and self.is_markup(self.index - 1):
            self.index -= 1

        return self.chunks[self.index]

    def is_command_block(self, index: int) -> bool:
        match self.chunks[index]:
            case CodeBlock(type="sh"):
                return True
            case _:
                return False

    def is_markup(self, index: int) -> bool:
        match self.chunks[index]:
            case Markup():
                return True
            case _:
                return False
