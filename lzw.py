import argparse
import os
import struct
from collections import namedtuple
from lzw_algo import FileCompressor, FileDecompressor
from prettytable import PrettyTable
import warnings

Header = namedtuple('Header', ['mode', 'atime', 'mtime',
                               'hash', 'c_size', 'size',
                               'path_length', 'path', 'name_length', 'name'])

warnings.formatwarning = lambda m, c, fn, ln, file=None, line=None: f'{m}\n'


def get_args():
    arg_parser = argparse.ArgumentParser(
        description='Архивирование и разархивирование в формате LZW')
    subparsers = arg_parser.add_subparsers(help='Список команд')

    compress_parser = subparsers.add_parser('compress', help='Архивирование')
    compress_parser.set_defaults(which='compress')
    compress_parser.add_argument('archive_name', type=str, help='Имя архива')
    compress_parser.add_argument('to_compress', nargs='+',
                                 help='Файлы и каталоги для архивирования')

    decompress_parser = subparsers.add_parser('decompress',
                                              help='Разархивирование')
    decompress_parser.set_defaults(which='decompress')
    decompress_parser.add_argument('archive_name', type=argparse.FileType(),
                                   help='Архив')
    decompress_parser.add_argument('-d', '--dir', default='.',
                                   help='Выходнй каталог')
    decompress_parser.add_argument('-r', '--restore-metadata',
                                   action='store_true', dest='restore',
                                   help='Востановить метаданные файлов')
    group = decompress_parser.add_mutually_exclusive_group()
    group.add_argument('-i', '--ignore-damage', action='store_true',
                       dest='ignore_damage',
                       help='Разархивровать все файлы, игнорируя повреждения')
    group.add_argument('-a', '--archive-not-damage',
                       action='store_true', dest='archive_not_damage',
                       help='Разархивровать, если архив не поврежден')
    group.add_argument('-f', '--files-not-damage',
                       action='store_true', dest='files_not_damage',
                       help='Разархивровать только неповрежденные файлы')

    listing_parser = subparsers.add_parser('listing',
                                           help='Просмотр файлов архива')
    listing_parser.set_defaults(which='listing')
    listing_parser.add_argument('archive_name', type=argparse.FileType(),
                                help='Архив')
    listing_parser.add_argument('-v', '--verbose', action='store_true',
                                help='Подробная информация')

    return arg_parser


class Compressor:
    def __init__(self, archive_name, files):
        self.files = files
        self.f_count = bytes([len(files)])
        self.archive_d = open(archive_name, 'wb')
        self.archive_d.write(self.f_count)

    def compress(self):
        for path, name, file in self.files:
            self.archive_d.write(bytes(53 + len(path) + len(name)))
            with open(file, 'rb') as file_d:
                c_size, hash_ = \
                    FileCompressor(file_d, self.archive_d).compress()
            self.write_file_header(path, name, file, c_size, hash_)

    def write_file_header(self, path, name, file, c_size, hash_):
        stat = os.stat(file)
        header = Header(
            struct.pack('H', stat.st_mode),
            struct.pack('d', stat.st_atime),
            struct.pack('d', stat.st_mtime),
            hash_,
            struct.pack('Q', c_size),
            struct.pack('Q', stat.st_size),
            struct.pack('H', len(path)),
            path.encode(),
            struct.pack('B', len(name)),
            name.encode(),
        )
        self.archive_d.seek(-(53 + len(path) + len(name) + c_size), 1)
        self.archive_d.write(b''.join([*header]))
        self.archive_d.seek(c_size, 1)

    def __del__(self):
        self.archive_d.close()


class Decompressor:
    def __init__(self, archive_name, directory, restore,
                 ignore_damage, archive_not_damage, files_not_damage):
        self.directory = directory
        if not os.path.exists(directory):
            os.makedirs(directory)
        self.restore = restore
        self.ignore_damage = ignore_damage
        self.archive_not_damage = archive_not_damage
        self.files_not_damage = files_not_damage
        if not (ignore_damage or archive_not_damage or files_not_damage):
            self.ignore_damage = True
        self.archive_d = open(archive_name, 'rb')
        self.f_count = self.archive_d.read(1)[0]

    def decompress(self):
        unpacked_files = []
        for _ in range(self.f_count):
            try:
                header = read_file_header(self.archive_d)
                dir_ = os.path.join(self.directory, header.path)
                if not os.path.exists(dir_):
                    os.makedirs(dir_)
                file = os.path.join(dir_, header.name)
                with open(file, 'wb') as file_d:
                    hash_ = FileDecompressor(self.archive_d, file_d,
                                             header.c_size).decompress()
                unpacked_files.append(file)
                if self.restore:
                    os.chmod(file, header.mode)
                    os.utime(file, (header.atime, header.mtime))
                assert hash_ == header.hash
            except (AssertionError, KeyError):
                if self.ignore_damage:
                    warnings.warn(f'{header.name} damaged!')
                    continue
                if self.archive_not_damage:
                    warnings.warn('Archive not unpacked. Damage!')
                    for file in unpacked_files:
                        os.remove(file)
                    break
                if self.files_not_damage:
                    warnings.warn(f'{header.name} not unpacked. Damage!')
                    os.remove(file)
                    continue

    def __del__(self):
        self.archive_d.close()


def read_file_header(archive_d):
    stat = [
        struct.unpack('H', archive_d.read(2))[0],
        struct.unpack('d', archive_d.read(8))[0],
        struct.unpack('d', archive_d.read(8))[0],
        archive_d.read(16),
        struct.unpack('Q', archive_d.read(8))[0],
        struct.unpack('Q', archive_d.read(8))[0],
        struct.unpack('H', archive_d.read(2))[0]
    ]
    path = archive_d.read(stat[6]).decode()
    name_length = struct.unpack('B', archive_d.read(1))[0]
    name = archive_d.read(name_length).decode()
    return Header(*stat, path, name_length, name)


def get_all_files_headers(archive_name):
    headers = []
    with open(archive_name, 'rb') as archive_d:
        f_count = archive_d.read(1)[0]
        for _ in range(f_count):
            header = read_file_header(archive_d)
            headers.append(header)
            archive_d.seek(header.c_size, 1)
    return headers


def listing(archive_name, verbose):
    headers = get_all_files_headers(archive_name)
    if verbose:
        table = PrettyTable(['NAME', 'RATE (%)',
                             'COMPRESSION SIZE (kB)', 'ORIGINAL SIZE (kB)'])
        for header in headers:
            table.add_row(
                [os.path.normpath(os.path.join(header.path, header.name)),
                 int((1 - header.c_size / header.size) * 100),
                 format(header.c_size / 1024, '.1f'),
                 format(header.size / 1024, '.1f')])
        print(table)
    else:
        for header in headers:
            print(os.path.normpath(os.path.join(header.path, header.name)))


def get_files_with_path_and_name(to_compress):
    res = []
    dirs = []
    for c in to_compress:
        if os.path.isfile(c):
            res.append(('./', os.path.basename(c), c))
        else:
            dirs.append(c)
    for d in dirs:
        dirname = os.path.dirname(d)
        for path, _, files in os.walk(d):
            res += [(os.path.relpath(path, start=dirname),
                     file, os.path.join(path, file)) for file in files]
    return res


if __name__ == '__main__':
    args = get_args().parse_args()
    if args.which == 'compress':
        Compressor(args.archive_name,
                   get_files_with_path_and_name(args.to_compress)).compress()
    elif args.which == 'decompress':
        Decompressor(args.archive_name.name, args.dir, args.restore,
                     args.ignore_damage, args.archive_not_damage,
                     args.files_not_damage).decompress()
    elif args.which == 'listing':
        listing(args.archive_name.name, args.verbose)
