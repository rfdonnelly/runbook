from typing import TextIO


class Writer:
    writer: TextIO

    def __init__(self, writer: TextIO):
        self.writer = writer

    def writenewline(self) -> None:
        self.writer.write("\n")

    def writelines(self, lines: list[str]) -> None:
        self.writer.writelines(lines)

    def write_command_block(self, lines: list[str]) -> None:
        pass

    def write_output_block(self, lines: list[str]) -> None:
        pass


class AsciidocWriter(Writer):
    def __init__(self, writer: TextIO):
        super().__init__(writer)

    def write_command_block(self, lines: list[str]) -> None:
        self.writer.write("[source,sh]\n")
        self.writer.write("----\n")
        self.writer.writelines(lines)
        self.writer.write("----\n")
        self.writenewline()

    def write_output_block(self, lines: list[str]) -> None:
        self.writer.write("[source,console]\n")
        self.writer.write(".Example\n")
        self.writer.write("----\n")
        self.writer.writelines(lines)
        self.writer.write("----\n")
        self.writenewline()


class MarkdownWriter(Writer):
    def __init__(self, writer: TextIO):
        super().__init__(writer)

    def write_command_block(self, lines: list[str]) -> None:
        self.writer.write("```sh\n")
        self.writer.writelines(lines)
        self.writer.write("```\n")
        self.writenewline()

    def write_output_block(self, lines: list[str]) -> None:
        self.writer.write("Example\n")
        self.writer.write("```console\n")
        self.writer.writelines(lines)
        self.writer.write("```\n")
        self.writenewline()


class Writers(Writer):
    writers: list[Writer]

    def __init__(self, writers: list[Writer]):
        self.writers = writers

    def writenewline(self) -> None:
        for writer in self.writers:
            writer.writenewline()

    def writelines(self, lines: list[str]) -> None:
        for writer in self.writers:
            writer.writelines(lines)

    def write_command_block(self, lines: list[str]) -> None:
        for writer in self.writers:
            writer.write_command_block(lines)

    def write_output_block(self, lines: list[str]) -> None:
        for writer in self.writers:
            writer.write_output_block(lines)
