import sys

import runbook.cli.filter
import runbook.cli.run


def main() -> None:
    command, *arguments = sys.argv[1:]

    match command:
        case "run":
            run.main(*arguments)
        case "filter":
            filter.main(*arguments)
