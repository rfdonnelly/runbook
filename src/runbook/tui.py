from io import StringIO
from pathlib import Path
import sys

import pydowndoc
from textual import log
from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Markdown, Rule
from textual.containers import VerticalScroll, HorizontalGroup

from runbook.reader import AsciidocReader, Markup, CodeBlock, Chunk
from runbook.writer import Writers, AsciidocWriter, MarkdownWriter

def markdown_chunks() -> list[Chunk]:
    ifile = open("examples/basic.adoc", "r")
    ofile = StringIO()
    log(ifile.read())
    ifile.seek(0)

    reader = AsciidocReader(ifile)
    chunks = list(reader)

    for chunk in chunks:
        asciidoc = "".join(chunk.lines).strip()
        if not asciidoc:
            continue
        markdown = pydowndoc.convert_string(asciidoc)
        chunk.lines = markdown.splitlines(keepends=True)
        chunks.append(chunk)

    return chunks

class Command(HorizontalGroup):
    def __init__(self, text: str) -> None:
        self.text = text
        super().__init__()

    def compose(self) -> ComposeResult:
        widget = Markdown(self.text)
        widget.styles.border_left = ("solid", "blue")
        yield widget


class RunbookApp(App):
    def compose(self) -> ComposeResult:
        yield Header()
        with VerticalScroll():
            for chunk in markdown_chunks():
                text = "".join(chunk.lines)
                match chunk:
                    case CodeBlock(type="sh"):
                        widget = Command(text)
                    case _:
                        widget = Markdown(text)
                yield widget
        yield Footer()


def main() -> None:
    app = RunbookApp()
    app.run()
