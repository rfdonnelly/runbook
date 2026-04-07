from pathlib import Path
import subprocess
import sys
from tempfile import NamedTemporaryFile

from runbook.tmux import Tmux
from runbook.reader import AsciidocReader, Markup, CodeBlock
from runbook.writer import Writers, AsciidocWriter, MarkdownWriter


def edit_command(command: str) -> str:
    with NamedTemporaryFile() as tfile:
        tfile.write(command.encode())
        tfile.flush()
        subprocess.run(["vim", tfile.name])
        tfile.seek(0)
        return tfile.read().decode().strip()


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

    for chunk in reader:
        match chunk:
            case Markup():
                # FIXME: Shouldn't return blank chunks (see test_adocreader)
                if chunk.lines:
                    writer.writelines(chunk.lines)
                    writer.writenewline()
                    print("".join(chunk.lines))
            case CodeBlock():
                match chunk.type:
                    case "sh":
                        captures = []
                        commands = []
                        for line in chunk.body:
                            command = line.strip()
                            print(f"$ {command}")
                            response = input("Execute [y]/n/e? ")
                            match response:
                                case "e":
                                    command = edit_command(command)
                                    commands.append(command + "\n")
                                    capture = target_pane.execute_and_capture_command(
                                        command
                                    )
                                    captures.extend(capture)
                                case "n":
                                    commands.append(command + "\n")
                                    captures.append(f"$ {command}\n")
                                    captures.append("NOT EXECUTED\n")
                                    continue
                                case _:
                                    commands.append(command + "\n")
                                    capture = target_pane.execute_and_capture_command(
                                        command
                                    )
                                    captures.extend(capture)

                        writer.write_command_block(commands)
                        writer.write_output_block(captures)
                        print()
                        print("".join(captures))

                    case "console":
                        pass

    target_pane.pane.kill()
