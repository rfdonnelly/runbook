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


def write_results(book: Book, path_stem: str) -> None:
    ofile_adoc = path_stem + "-result.adoc"
    ofile_md = path_stem + "-result.md"
    ofile_adoc = open(ofile_adoc, "w")
    ofile_md = open(ofile_md, "w")
    writer = Writers([AsciidocWriter(ofile_adoc), MarkdownWriter(ofile_md)])

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

    ofile_adoc.close()
    ofile_md.close()


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
                    erase_line()
                    return default_char
            case _:
                if value in valid_chars:
                    erase_line()
                    return value


def erase_line() -> None:
    print("\r\033[K", end="", flush=True)


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
    ifile_path = Path(sys.argv[1])
    ifile = open(ifile_path, "r")
    reader = AsciidocReader(ifile)

    tmux = Tmux()

    book = Book(reader)
    chunk = book.first_chunk()

    while True:
        match chunk:
            case Markup():
                # FIXME: Shouldn't return blank chunks (see test_adocreader)
                if chunk.lines:
                    print("".join(chunk.lines))
            case CodeBlock(type="sh"):
                print("".join(chunk.body))
                response = inputkey(
                    "E[X]ecute/[n]ext/[e]dit/[p]revious/[q]uit? ", "xnepq", "x"
                )
                match response:
                    case "e":
                        chunk.body = edit_command(chunk.body)
                        if chunk.shell_new and chunk.shell_id != "default":
                            tmux.create_shell(chunk.shell_id)
                        if chunk.shell_id != "default":
                            chunk.captures = tmux.shells[
                                chunk.shell_id
                            ].execute_and_manual_capture_commands(chunk.body)
                        else:
                            chunk.captures = tmux.shells[
                                chunk.shell_id
                            ].execute_and_capture_commands(chunk.body)
                        write_results(book, ifile_path.stem)
                    case "n":
                        pass
                    case "p":
                        chunk = book.prev_command_block()
                        continue
                    case "x":
                        if chunk.shell_new and chunk.shell_id != "default":
                            tmux.create_shell(chunk.shell_id)
                        if chunk.shell_id != "default":
                            chunk.captures = tmux.shells[
                                chunk.shell_id
                            ].execute_and_manual_capture_commands(chunk.body)
                        else:
                            chunk.captures = tmux.shells[
                                chunk.shell_id
                            ].execute_and_capture_commands(chunk.body)
                        write_results(book, ifile_path.stem)
                    case "q":
                        break

        if book.next_chunk_exists():
            chunk = book.next_chunk()
        else:
            break

    response = inputkey("Execution complete. Close panes? (y/n) ", "yn")
    match response:
        case "y":
            for id, shell in tmux.shells.items():
                shell.kill()
