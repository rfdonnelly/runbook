from pathlib import Path
import random
import string
import subprocess
import sys
from tempfile import NamedTemporaryFile
import time

import libtmux
from libtmux.constants import PaneDirection

from runbook.reader import AsciidocReader, Markup, CodeBlock
from runbook.writer import Writers, AsciidocWriter, MarkdownWriter


def create_shellrc() -> NamedTemporaryFile:
    shellrc = NamedTemporaryFile()
    shellrc.write(br"export PS1='\[\033[01;32m\]\u@\h\[\033[00m\]:\[\033[01;34m\]\w\[\033[00m\]\$ '")
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
    try:
        start_index = text.index(marker)
    except ValueError:
        text = pane.capture_pane(start="-", join_wrapped=True)
        start_index = text.index(marker)


    # Extract output (everything after marker minus next prompt)
    text = text[start_index + 1 : -1]

    # Trim end marker
    text[0], _ = text[0].rsplit(";")

    text = [line + "\n" for line in text]

    return text


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

    tmux = libtmux.Server()

    host_pane = tmux.sessions[0].active_pane

    shellrc = create_shellrc()
    target_pane = create_pane(host_pane, shellrc.name)

    while chunk := reader.next_chunk():
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
                                    capture = execute_and_capture_command(
                                        target_pane, command
                                    )
                                    captures.extend(capture)
                                case "n":
                                    commands.append(command + "\n")
                                    captures.append(f"$ {command}\n")
                                    captures.append("NOT EXECUTED\n")
                                    continue
                                case _:
                                    commands.append(command + "\n")
                                    capture = execute_and_capture_command(
                                        target_pane, command
                                    )
                                    captures.extend(capture)

                        writer.write_command_block(commands)
                        writer.write_output_block(captures)
                        print()
                        print("".join(captures))

                    case "console":
                        pass

    target_pane.kill()
