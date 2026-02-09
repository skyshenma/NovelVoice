
import unittest
import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.text_splitter import TextSplitter

class TestTextSplitter(unittest.TestCase):
    def setUp(self):
        self.splitter = TextSplitter()

    def test_basic_split(self):
        text = "Hello world. This is a test."
        # max_chars=10, should split at "Hello world." (12 chars > 10? No wait)
        # "Hello world." is 12 chars.
        chunks = self.splitter.split_text(text, max_chars=15)
        self.assertEqual(len(chunks), 2)
        self.assertEqual(chunks[0], "Hello world. ")
        self.assertEqual(chunks[1], "This is a test.")

    def test_paragraph_split(self):
        text = "Para 1.\n\nPara 2 is longer."
        chunks = self.splitter.split_text(text, max_chars=10)
        # "Para 1.\n\n" is 9 chars.
        # "Para 2 is longer." is 17 chars. -> Split "Para 2 is " and "longer."?
        
        self.assertEqual(chunks[0], "Para 1.\n\n")
        self.assertTrue(len(chunks) >= 2)

    def test_chinese_split(self):
        text = "第一句。第二句很长很长很长。第三句。"
        # "第一句。" = 4 chars
        # "第二句很长很长很长。" = 11 chars
        # "第三句。" = 4 chars
        
        chunks = self.splitter.split_text(text, max_chars=6)
        # Should split: "第一句。", "第二句...", "很长...", "第三句。"
        self.assertEqual(chunks[0], "第一句。")
        self.assertTrue(len(chunks) >= 3)
        
    def test_no_split_needed(self):
        text = "Short text."
        chunks = self.splitter.split_text(text, max_chars=50)
        self.assertEqual(len(chunks), 1)
        self.assertEqual(chunks[0], "Short text.")

if __name__ == '__main__':
    unittest.main()
