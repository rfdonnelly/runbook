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
            shell_id="default",
            shell_new=True
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

    def test_multishell(self):
        input = """\
            [source,sh]
            ----
            command
            ----

            [source,sh,id=2]
            ----
            command2
            ----

            [source,sh,id=2]
            ----
            command3
            ----
        """
        input = textwrap.dedent(input)
        reader = AsciidocReader(StringIO(input))

        # FIXME: Shouldn't return blank chunks
        expected = Markup([])
        assert next(reader) == expected

        expected = CodeBlock(
            type="sh",
            lines=[
                "[source,sh]\n",
                "----\n",
                "command\n",
                "----\n",
            ],
            body=[
                "command\n",
            ],
            shell_id="default",
            shell_new=True
        )
        assert next(reader) == expected

        # FIXME: Shouldn't return blank chunks
        expected = Markup([])
        assert next(reader) == expected

        expected = CodeBlock(
            type="sh",
            lines=[
                "[source,sh,id=2]\n",
                "----\n",
                "command2\n",
                "----\n",
            ],
            body=[
                "command2\n",
            ],
            shell_id="2",
            shell_new=True
        )
        assert next(reader) == expected

        # FIXME: Shouldn't return blank chunks
        expected = Markup([])
        assert next(reader) == expected

        expected = CodeBlock(
            type="sh",
            lines=[
                "[source,sh,id=2]\n",
                "----\n",
                "command3\n",
                "----\n",
            ],
            body=[
                "command3\n",
            ],
            shell_id="2",
            shell_new=False
        )
        assert next(reader) == expected
