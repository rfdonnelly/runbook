from runbook.book import Book
from runbook.datamodel import Chunk, Markup, CodeBlock

class TestBook:
    def test_basic(self):
        chunks = [
                Markup(["1"]),
                CodeBlock("sh", ["2"]),
                CodeBlock("sh", ["3"]),
                Markup(["4"]),
                CodeBlock("sh", ["5"]),
                ]
        book = Book(chunks)

        assert book.first_chunk() == chunks[0]
        assert book.next_chunk() == chunks[1]
        assert book.next_chunk() == chunks[2]
        assert book.next_chunk() == chunks[3]
        assert book.next_chunk() == chunks[4]
        assert book.prev_chunk() == chunks[3]
        assert book.next_chunk() == chunks[4]
        assert book.prev_command_block() == chunks[2]
        assert book.prev_command_block() == chunks[0]
