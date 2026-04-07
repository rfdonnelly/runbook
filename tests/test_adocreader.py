import textwrap
from io import StringIO

import pytest

from runbook.reader import AsciidocReader
from runbook.datamodel import Markup, CodeBlock


class TestAsciidocReader:
    def test_basic(self):
        input = """\
            = Title

            [source,sh]
            .Caption
            ----
            command
            ----

            [source,console]
            .Example
            ----
            $ command
            output
            ----
        """
        input = textwrap.dedent(input)
        reader = AsciidocReader(StringIO(input))
        expected = Markup(
            [
                "= Title\n",
            ]
        )
        assert next(reader) == expected

        expected = CodeBlock(
            type="sh",
            lines=[
                "[source,sh]\n",
                ".Caption\n",
                "----\n",
                "command\n",
                "----\n",
            ],
            body=[
                "command\n",
            ],
        )
        assert next(reader) == expected

        # FIXME: Shouldn't return blank chunks
        expected = Markup([])
        assert next(reader) == expected

        expected = CodeBlock(
            type="console",
            lines=[
                "[source,console]\n",
                ".Example\n",
                "----\n",
                "$ command\n",
                "output\n",
                "----\n",
            ],
            body=[
                "$ command\n",
                "output\n",
            ],
        )
        assert next(reader) == expected

        with pytest.raises(StopIteration):
            next(reader)
