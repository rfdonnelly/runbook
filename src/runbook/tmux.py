import random
import string
from tempfile import NamedTemporaryFile
import time

import libtmux
from libtmux.constants import PaneDirection


class TmuxPane:
    pane: libtmux.Pane

    def __init__(self, pane: libtmux.Pane):
        self.pane = pane

    def execute_and_capture_commands(self, commands: list[str]) -> list[str]:
        captures = []

        for command in commands:
            capture = self.execute_and_capture_command(command.strip())
            captures.extend(capture)

        return captures

    def execute_and_capture_command(self, command: str) -> list[str]:
        """
        Executes a command in the provided pane and returns the output including
        prompt and command.

        Inserts a unique marker to mark the start of the output.  Command
        completion is signaled via the tmux window name.
        """

        marker = self.create_marker()
        saved_window_name = self.pane.window.name

        self.pane.send_keys(f"echo {marker}")
        self.pane.send_keys(f"{command}; tmux rename-window {marker}")

        # Wait for command to complete. Completion is signaled by rename-window.
        while self.pane.window.name != marker:
            time.sleep(0.1)
        self.pane.window.rename_window(saved_window_name)

        text = self.pane.capture_pane(join_wrapped=True)
        try:
            start_index = text.index(marker)
        except ValueError:
            text = self.pane.capture_pane(start="-", join_wrapped=True)
            start_index = text.index(marker)

        # Extract output (everything after marker minus next prompt)
        text = text[start_index + 1 : -1]

        # Trim end marker
        text[0], _ = text[0].rsplit(";")

        text = [line + "\n" for line in text]

        return text

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
    host_pane: TmuxPane

    def __init__(self):
        self.shellrc = self.create_shellrc()
        self.server = libtmux.Server()
        self.host_pane = TmuxPane(self.server.sessions[0].active_pane)

    @staticmethod
    def create_shellrc() -> NamedTemporaryFile:
        shellrc = NamedTemporaryFile()
        shellrc.write(
            rb"export PS1='\[\033[01;32m\]\u@\h\[\033[00m\]:\[\033[01;34m\]\w\[\033[00m\]\$ '"
        )
        shellrc.flush()
        return shellrc

    def create_pane(self, relative_to: TmuxPane) -> TmuxPane:
        return TmuxPane(
            relative_to.pane.split(
                direction=PaneDirection.Right,
                shell=f"bash --rcfile {self.shellrc.name} -i",
            )
        )
