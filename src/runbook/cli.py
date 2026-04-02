from pathlib import Path
import random
import string
import sys
from tempfile import NamedTemporaryFile
import time

import libtmux
from libtmux.constants import PaneDirection

from runbook.reader import AsciidocReader, Markup, CodeBlock
from runbook.writer import Writers, AsciidocWriter, MarkdownWriter


def create_shellrc() -> NamedTemporaryFile:
    shellrc = NamedTemporaryFile()
    shellrc.write(b"export PS1='\u@\h:\w\$ '\n")
    shellrc.flush()
    return shellrc


def create_pane(relative_to: libtmux.Pane, bashrc: str) -> libtmux.Pane:
    return relative_to.split(
        direction=PaneDirection.Right, shell=f"bash --rcfile {bashrc} -i"
    )


def create_marker() -> str:
    length = 32
    characters = string.ascii_letters + string.digits
    random_characters = random.choices(characters, k=length)
    random_string = "".join(random_characters)
    return random_string


def execute_and_capture_command(pane: libtmux.Pane, command: str) -> list[str]:
    """
    Executes a command in the provided pane and returns the output including
    prompt and command.

    Inserts a unique marker to mark the start of the output.  Command
    completion is signaled via the tmux window name.
    """

    marker = create_marker()
    saved_window_name = pane.window.name

    pane.send_keys(f"echo {marker}")
    pane.send_keys(f"{command}; tmux rename-window {marker}")

    # Wait for command to complete. Completion is signaled by rename-window.
    while pane.window.name != marker:
        time.sleep(0.1)
    pane.window.rename_window(saved_window_name)

    text = pane.capture_pane(join_wrapped=True)

    start_index = text.index(marker)

    # Extract output (everything after marker minus next prompt)
    text = text[start_index + 1 : -1]

    # Trim end marker
    text[0], _ = text[0].rsplit(";")

    text = [line + "\n" for line in text]

    return text


def main() -> None:
    ifile = Path(sys.argv[1])
    ofile_adoc = ifile.stem + ".adoc"
    ofile_md = ifile.stem + ".md"
    ifile = open(ifile, "r")
    ofile_adoc = open(ofile_adoc, "w")
    ofile_md = open(ofile_md, "w")
    reader = AsciidocReader(ifile)
    writer = Writers([AsciidocWriter(ofile_adoc), MarkdownWriter(ofile_md)])

    tmux = libtmux.Server()

    host_pane = tmux.sessions[0].active_pane

    shellrc = create_shellrc()
    target_pane = create_pane(host_pane, shellrc.name)

    while chunk := reader.next_chunk():
        match chunk:
            case Markup():
                writer.writelines(chunk.lines)
                print("".join(chunk.lines))
            case CodeBlock():
                match chunk.type:
                    case "sh":
                        writer.write_command_block(chunk.body)
                        writer.writelines(["\n"])

                        capture_cummulative = []
                        for line in chunk.body:
                            command = line.strip()
                            print(f"$ {command}")
                            response = input("Execute [y]/n? ")
                            match response:
                                case "n":
                                    capture_cummulative.append(f"$ {command}\n")
                                    capture_cummulative.append("NOT EXECUTED\n")
                                    continue
                                case _:
                                    capture = execute_and_capture_command(
                                        target_pane, command
                                    )
                                    capture_cummulative.extend(capture)

                        writer.write_output_block(capture_cummulative)
                        print()
                        print("".join(capture))

                    case "console":
                        pass

    target_pane.kill()
