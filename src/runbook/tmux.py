import random
import string
from tempfile import NamedTemporaryFile
import time

import libtmux
from libtmux.constants import PaneDirection


class Shell:
    pane: libtmux.Pane

    def __init__(self, pane: libtmux.Pane):
        self.pane = pane

    def kill(self) -> None:
        self.pane.kill()

    def execute_and_capture_commands(self, commands: list[str]) -> list[str]:
        captures = []

        for command in commands:
            capture = self.execute_and_capture_command(command.strip())
            captures.extend(capture)

        return captures

    def execute_and_capture_command(self, command: str) -> list[str]:
        """
        Executes a command and returns the output including prompt and command.

        Inserts a unique marker to mark the start of the output.  Command
        completion is signaled via the tmux window name.
        """

        marker = self.create_marker()
        window_id = self.pane.window.id
        saved_window_name = self.pane.window.name

        if command.endswith(" &"):
            command = command.rstrip(" &")
            marker_separator = " &"
        else:
            marker_separator = ";"

        self.pane.send_keys(
            f"{command}{marker_separator} tmux rename-window -t {window_id} {marker}"
        )

        # Wait for command to complete. Completion is signaled by rename-window.
        while self.pane.window.name != marker:
            time.sleep(0.1)
        self.pane.window.rename_window(saved_window_name)

        return self.capture(marker, marker_separator)

    def capture(self, marker: str, marker_separator: str) -> list[str]:
        lines = self.pane.capture_pane(join_wrapped=True)
        try:
            # Try capturing only visible text first
            start_index = next(
                (index for (index, line) in enumerate(lines) if line.endswith(marker))
            )
            lines = lines[start_index:-1]

            # Trim end marker
            lines[0], _ = lines[0].rsplit(marker_separator, 1)
        except StopIteration:
            try:
                # Fall back to capturing entire scrollback buffer
                lines = self.pane.capture_pane(start="-", join_wrapped=True)
                start_index = next(
                    (
                        index
                        for (index, line) in enumerate(lines)
                        if line.endswith(marker)
                    )
                )
                lines = lines[start_index:-1]

                # Trim end marker
                lines[0], _ = lines[0].rsplit(marker_separator, 1)
            except StopIteration:
                # Fall back to captuing entire scrollback buffer w/o prompt + command
                lines = ["<< SCROLLBACK EXCEEDED >>", *lines[0:-1]]

        lines = [line.rstrip() + "\n" for line in lines]

        return lines

    def execute_and_manual_capture_commands(self, commands: list[str]) -> list[str]:
        captures = []

        for command in commands:
            capture = self.execute_and_manual_capture_command(command.strip())
            captures.extend(capture)

        return captures

    def execute_and_manual_capture_command(self, command: str) -> list[str]:
        marker = self.create_marker()

        self.pane.send_keys(f"{command} # {marker}")

        input("Press enter when command is complete")

        return self.capture(marker, " #")

    @staticmethod
    def create_marker() -> str:
        length = 32
        characters = string.ascii_letters + string.digits
        random_characters = random.choices(characters, k=length)
        random_string = "".join(random_characters)
        return random_string


class Tmux:
    shellrc: NamedTemporaryFile
    server: libtmux.Server
    most_recent_pane: libtmux.Pane
    shells: dict[str, Shell]

    def __init__(self):
        self.shellrc = self.create_shellrc()
        self.server = libtmux.Server()
        self.most_recent_pane = self.server.sessions[0].active_pane
        self.shells = dict()
        self.create_shell("default")

    @staticmethod
    def create_shellrc() -> NamedTemporaryFile:
        shellrc = NamedTemporaryFile()
        shellrc.write(
            rb"export PS1='\[\033[01;32m\]\u@\h\[\033[00m\]:\[\033[01;34m\]\w\[\033[00m\]\$ '"
        )
        shellrc.flush()
        return shellrc

    def create_shell(self, id: str) -> Shell:
        new_pane = self.most_recent_pane.split(
            direction=PaneDirection.Right,
            shell=f"bash --rcfile {self.shellrc.name} -i",
        )
        new_pane.window.select_layout("even-horizontal")
        self.most_recent_pane = new_pane
        self.shells[id] = Shell(new_pane)
