from tempfile import NamedTemporaryFile
import subprocess


def edit_lines(commands: list[str], remove_blank_lines: bool = False) -> list[str]:
    with NamedTemporaryFile(mode="wt", delete_on_close=False) as wfile:
        wfile.writelines(commands)
        wfile.close()
        subprocess.run(["vim", wfile.name])
        with open(wfile.name, mode="rt") as rfile:
            lines = rfile.readlines()
            if remove_blank_lines:
                lines = [line for line in lines if line != "\n"]
            return lines
