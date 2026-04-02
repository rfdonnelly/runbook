from typing import TextIO


class AdocWriter:
    writer: TextIO

    def __init__(self, writer: TextIO):
        self.writer = writer

    def writelines(self, lines: list[str]) -> None:
        self.writer.writelines(lines)

    def write_output_block(self, lines: list[str]) -> None:
        self.writer.write("[source,console]\n")
        self.writer.write(".Output\n")
        self.writer.write("----\n")
        self.writer.writelines(lines)
        self.writer.write("----\n")
