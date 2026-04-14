import textwrap
from io import StringIO

from runbook.writer import AsciidocWriter


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
        writer.write_output_block(["1\n", "2\n"])
        expected = textwrap.dedent("""\
            [source,console]
            .Example
            ----
            1
            2
            ----

        """)
        assert output.getvalue() == expected
