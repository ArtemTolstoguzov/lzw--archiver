import unittest
import os
import sys
from io import BytesIO

sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                             os.path.pardir))
import lzw
from lzw_algo import FileCompressor


class CompressorTest(unittest.TestCase):
    def test_write_correct_file_header(self):
        lzw.Compressor(
            'tests/arch.lzw',
            lzw.get_files_with_path_and_name(['tests/files/0.txt'])).compress()
        with open('tests/files/0.txt', 'rb') as f_d:
            c_size, hash_ = FileCompressor(f_d, BytesIO()).compress()
        stat = os.stat('tests/files/0.txt')
        c_header = [
            stat.st_mode,
            stat.st_atime,
            stat.st_mtime,
            hash_,
            c_size,
            stat.st_size,
            len('./'),
            './',
            len('0.txt'),
            '0.txt'
        ]
        with open('tests/arch.lzw', 'rb') as a_d:
            a_d.read(1)
            r_header = lzw.read_file_header(a_d)
        os.remove('tests/arch.lzw')
        self.assertListEqual(c_header, [*r_header])


class FuncTest(unittest.TestCase):
    def test_get_all_files_headers(self):
        files = ['tests/files/0.txt', 'tests/files/1.txt', 'tests/files/2.txt']
        lzw.Compressor('tests/arch.lzw',
                       lzw.get_files_with_path_and_name(files)).compress()
        headers = lzw.get_all_files_headers('tests/arch.lzw')
        os.remove('tests/arch.lzw')
        self.assertSetEqual(set(h.name for h in headers),
                            set(os.listdir('tests/files')))

    def test_get_args(self):
        args = lzw.get_args()
        self.assertIsNotNone(args)

    def test_get_files_with_path_and_name(self):
        res = lzw.get_files_with_path_and_name(['tests/files',
                                                'tests/test_lzw_algo.py'])
        self.assertSetEqual(
            {('./', 'test_lzw_algo.py', 'tests/test_lzw_algo.py'),
             ('files', '2.txt', 'tests/files/2.txt'),
             ('files', '1.txt', 'tests/files/1.txt'),
             ('files', '0.txt', 'tests/files/0.txt')}, set(res))


class DecompressorTest(unittest.TestCase):
    def tearDown(self):
        os.remove('tests/arch.lzw')

    def test_dir_exist(self):
        lzw.Compressor(
            'tests/arch.lzw',
            lzw.get_files_with_path_and_name(['tests/files/0.txt'])).compress()
        lzw.Decompressor('tests/arch.lzw', 'tests',
                         False, False, False, False).decompress()
        self.assertTrue(os.path.exists('tests/0.txt'))
        os.remove('tests/0.txt')

    def test_dir_not_exist(self):
        lzw.Compressor(
            'tests/arch.lzw',
            lzw.get_files_with_path_and_name(['tests/files/0.txt'])).compress()
        lzw.Decompressor('tests/arch.lzw', 'tests/a',
                         False, False, False, False).decompress()
        self.assertTrue(os.path.exists('tests/a/0.txt'))
        os.remove('tests/a/0.txt')
        os.removedirs('tests/a')

    def test_file_damaged_with_i(self):
        lzw.Compressor(
            'tests/arch.lzw',
            lzw.get_files_with_path_and_name(['tests/files/0.txt'])).compress()
        with open('tests/arch.lzw', 'rb+') as f:
            f.seek(-10, 2)
            f.write(b'\x00')
        with self.assertWarns(UserWarning):
            lzw.Decompressor('tests/arch.lzw', 'tests',
                             False, True, False, False).decompress()
        self.assertTrue(os.path.exists('tests/0.txt'))
        os.remove('tests/0.txt')

    def test_file_damaged_with_a(self):
        lzw.Compressor(
            'tests/arch.lzw',
            lzw.get_files_with_path_and_name(['tests/files/0.txt'])).compress()
        with open('tests/arch.lzw', 'rb+') as f:
            f.seek(-10, 2)
            f.write(b'\x00')
        with self.assertWarns(UserWarning):
            lzw.Decompressor('tests/arch.lzw', 'tests',
                             False, False, True, False).decompress()
        self.assertFalse(os.path.exists('tests/0.txt'))

    def test_file_damaged_with_f(self):
        lzw.Compressor(
            'tests/arch.lzw', lzw.get_files_with_path_and_name(
                ['tests/files/0.txt', 'tests/files/1.txt'])).compress()
        with open('tests/arch.lzw', 'rb+') as f:
            f.seek(-10, 2)
            f.write(b'\x00')
        with self.assertWarns(UserWarning):
            lzw.Decompressor('tests/arch.lzw', 'tests',
                             False, False, False, True).decompress()
        self.assertTrue(os.path.exists('tests/0.txt'))
        self.assertFalse(os.path.exists('tests/1.txt'))
        os.remove('tests/0.txt')

    def test_restore(self):
        lzw.Compressor(
            'tests/arch.lzw',
            lzw.get_files_with_path_and_name(['tests/files/0.txt'])).compress()
        stat = os.stat('tests/files/0.txt')
        c_md = [stat.st_mode, stat.st_atime, stat.st_mtime]
        lzw.Decompressor('tests/arch.lzw', 'tests',
                         True, False, False, True).decompress()
        stat = os.stat('tests/0.txt')
        r_md = [stat.st_mode, stat.st_atime, stat.st_mtime]
        self.assertListEqual(c_md, r_md)
        os.remove('tests/0.txt')


if __name__ == '__main__':
    unittest.main()
