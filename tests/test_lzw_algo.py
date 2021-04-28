import unittest
import os
import sys
from io import BytesIO
import random
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                             os.path.pardir))
from lzw_algo import FileCompressor, FileDecompressor


class AlgoTest(unittest.TestCase):
    file = None
    lzw_file = None
    x_file = None

    @staticmethod
    def do_lzw(min_, max_):
        AlgoTest.file = BytesIO(os.urandom(random.randint(min_, max_)))
        c_size, hash_ = FileCompressor(AlgoTest.file, AlgoTest.lzw_file)\
            .compress()
        AlgoTest.lzw_file.seek(0)
        FileDecompressor(AlgoTest.lzw_file, AlgoTest.x_file, c_size)\
            .decompress()

    def setUp(self):
        AlgoTest.file = BytesIO()
        AlgoTest.lzw_file = BytesIO()
        AlgoTest.x_file = BytesIO()

    def tearDown(self):
        AlgoTest.file.close()
        AlgoTest.lzw_file.close()
        AlgoTest.x_file.close()

    def test_small_file(self):
        AlgoTest.do_lzw(512, 1024)
        self.assertEqual(AlgoTest.file.getvalue(), AlgoTest.x_file.getvalue())

    def test_medium_file(self):
        AlgoTest.do_lzw(2 ** 20, 2 ** 21)
        self.assertEqual(AlgoTest.file.getvalue(), AlgoTest.x_file.getvalue())

    def test_large_file(self):
        AlgoTest.do_lzw(2 ** 24, 2 ** 25)
        self.assertEqual(AlgoTest.file.getvalue(), AlgoTest.x_file.getvalue())


if __name__ == '__main__':
    unittest.main()
