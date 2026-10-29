import sys
from pathlib import Path

from runbook.reader import AsciidocReader, CodeBlock, Markup
from runbook.writer import AsciidocWriter


def main(ifile_path: str) -> None:
    ifile_path = Path(ifile_path)
    ifile = open(ifile_path, "r")
    reader = AsciidocReader(ifile)
    writer = AsciidocWriter(sys.stdout)

    for chunk in reader:
        match chunk:
            case Markup():
                writer.write_markup(chunk)
            case CodeBlock(type="sh"):
                writer.write_command_block(chunk)
