from pathlib import Path
import subprocess
import sys
from tempfile import NamedTemporaryFile

from runbook.tmux import Tmux
from runbook.book import Book
from runbook.reader import AsciidocReader, Markup, CodeBlock
from runbook.writer import Writers, AsciidocWriter, MarkdownWriter


def edit_command(commands: list[str]) -> list[str]:
    with NamedTemporaryFile(mode="wt", delete_on_close=False) as wfile:
        wfile.writelines(commands)
        wfile.close()
        subprocess.run(["vim", wfile.name])
        with open(wfile.name, mode="rt") as rfile:
            return rfile.readlines()


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

    target_pane = tmux.create_pane(tmux.host_pane)

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
                response = input("E[X]ecute/[n]ext/[e]dit/[p]revious? ")
                match response:
                    case "e":
                        chunk.body = edit_command(chunk.body)
                        chunk.captures = target_pane.execute_and_capture_commands(
                            chunk.body
                        )
                        print("".join(chunk.captures))
                    case "n":
                        pass
                    case "p":
                        chunk = book.prev_command_block()
                        continue
                    case _:
                        chunk.captures = target_pane.execute_and_capture_commands(
                            chunk.body
                        )
                        print("".join(chunk.captures))

        if book.next_chunk_exists():
            chunk = book.next_chunk()
        else:
            break

    response = input("execution complete\nclose pane? (y/N)")
    match response:
        case "y":
            target_pane.pane.kill()

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
