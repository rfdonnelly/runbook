import textwrap
from io import StringIO

from runbook.writer import AsciidocWriter
from runbook.datamodel import CodeBlock


class TestAsciidocWriter:
    def test_writelines(self):
        output = StringIO()
        writer = AsciidocWriter(output)
        writer.writelines(["1\n", "2\n"])
        expected = textwrap.dedent("""\
            1
            2
        """)
        assert output.getvalue() == expected

    def test_write_output_block(self):
        output = StringIO()
        writer = AsciidocWriter(output)
        chunk = CodeBlock(
            type="sh",
            lines=[],
            body=[],
            captures=["1\n", "2\n"],
        )

        writer.write_output_block(chunk)
        expected = textwrap.dedent("""\
            [source,console]
            .Example
            ----
            1
            2
            ----

        """)
        assert output.getvalue() == expected
