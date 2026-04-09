import os
from pathlib import Path
import signal
import subprocess
import sys
from tempfile import NamedTemporaryFile

from readchar import readkey, key

from runbook.tmux import Tmux
from runbook.book import Book
from runbook.reader import AsciidocReader, Markup, CodeBlock
from runbook.writer import Writers, AsciidocWriter, MarkdownWriter


def inputkey(prompt: str, valid_chars: str, default_char: str | None = None) -> str:
    print(prompt, end="", flush=True)

    while True:
        value = readkey()
        match value:
            case key.CTRL_Z:
                os.kill(os.getpid(), signal.SIGSTOP)
                print(prompt, end="", flush=True)
            case key.ENTER:
                if default_char:
                    print("\r\033[K", end="", flush=True)
                    return default_char
            case _:
                if value in valid_chars:
                    print("\r\033[K", end="", flush=True)
                    return value


def edit_command(commands: list[str]) -> list[str]:
    with NamedTemporaryFile(mode="wt", delete_on_close=False) as wfile:
        wfile.writelines(commands)
        wfile.close()
        subprocess.run(["vim", wfile.name])
        with open(wfile.name, mode="rt") as rfile:
            lines = rfile.readlines()
            # filter blank lines
            lines = [line for line in lines if line != "\n"]
            return lines


def main() -> None:
    ifile = Path(sys.argv[1])
    ofile_adoc = ifile.stem + "-result.adoc"
    ofile_md = ifile.stem + "-result.md"
    ifile = open(ifile, "r")
    ofile_adoc = open(ofile_adoc, "w")
    ofile_md = open(ofile_md, "w")
    reader = AsciidocReader(ifile)
    writer = Writers([AsciidocWriter(ofile_adoc), MarkdownWriter(ofile_md)])

    tmux = Tmux()

    pane = tmux.create_pane(tmux.host_pane)

    book = Book(reader)
    chunk = book.first_chunk()

    while True:
        match chunk:
            case Markup():
                # FIXME: Shouldn't return blank chunks (see test_adocreader)
                if chunk.lines:
                    writer.writelines(chunk.lines)
                    writer.writenewline()
                    print("".join(chunk.lines))
            case CodeBlock(type="sh"):
                print("".join(chunk.body))
                response = inputkey(
                    "E[X]ecute/[n]ext/[e]dit/[p]revious/[q]uit? ", "xnepq", "x"
                )
                match response:
                    case "e":
                        chunk.body = edit_command(chunk.body)
                        chunk.captures = pane.execute_and_capture_commands(chunk.body)
                    case "n":
                        pass
                    case "p":
                        chunk = book.prev_command_block()
                        continue
                    case "x":
                        chunk.captures = pane.execute_and_capture_commands(chunk.body)
                    case "q":
                        break

        if book.next_chunk_exists():
            chunk = book.next_chunk()
        else:
            break

    for chunk in book.chunks:
        match chunk:
            case Markup():
                # FIXME: Shouldn't return blank chunks (see test_adocreader)
                if chunk.lines:
                    writer.writelines(chunk.lines)
                    writer.writenewline()
            case CodeBlock(type="sh"):
                writer.write_command_block(chunk.body)
                writer.write_output_block(chunk.captures)

    response = inputkey("Execution complete. Close pane? (y/n) ", "yn")
    match response:
        case "y":
            pane.kill()
