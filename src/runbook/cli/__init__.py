import sys

import runbook.cli.run

def main() -> None:
    command, *arguments = sys.argv[1:]

    match command:
        case "run":
            run.main(*arguments)
