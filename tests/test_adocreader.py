import textwrap
from io import StringIO

from runbook.reader import AdocReader, Chunk, ChunkType


class TestAdocReader:
    def test_basic(self):
        input = """\
            = Title

            [source,sh]
            .Caption
            ----
            command
            ----
        """
        input = textwrap.dedent(input)
        reader = AdocReader(StringIO(input))
        expected = Chunk(
            type=ChunkType.Markup,
            lines=[
                "= Title\n",
                "\n",
                "[source,sh]\n",
                ".Caption\n",
                "----\n",
            ],
        )
        assert reader.next_chunk() == expected

        expected = Chunk(
            type=ChunkType.CommandBlock,
            lines=[
                "command\n",
            ],
        )
        assert reader.next_chunk() == expected

        expected = Chunk(
            type=ChunkType.Markup,
            lines=[
                "----\n",
            ],
        )
        assert reader.next_chunk() == expected

        assert reader.next_chunk() is None
