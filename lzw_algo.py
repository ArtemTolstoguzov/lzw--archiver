import hashlib


class FileCompressor:
    def __init__(self, input_descriptor, output_descriptor, max_code_size=16):
        self.codes = {bytes([i]): i for i in range(256)}
        self.code_size = 9
        self.max_code = 2 ** max_code_size
        self.in_d = input_descriptor
        self.out_d = output_descriptor
        self.buff = 0
        self.pending_bits = 0
        self.next_code = 256
        self.current_string = b''
        self.hash = hashlib.md5()
        self.count = 0

    def compress(self):
        while True:
            byte = self.in_d.read(1)
            if byte == b'':
                self.end_compress()
                return self.count, self.hash.digest()

            self.current_string += byte
            if self.current_string in self.codes:
                continue

            self.flush()

            if self.next_code < self.max_code:
                self.codes[self.current_string] = self.next_code
                self.next_code += 1
                self.code_size = self.next_code.bit_length()

            self.current_string = byte

    def flush(self):
        self.buff |= self.codes[self.current_string[:-1]] << self.pending_bits
        self.pending_bits += self.code_size
        while self.pending_bits >= 8:
            byte = bytes([self.buff & 0xff])
            self.out_d.write(byte)
            self.count += 1
            self.hash.update(byte)
            self.buff >>= 8
            self.pending_bits -= 8

    def end_compress(self):
        self.current_string += b'\x00'
        self.flush()
        self.out_d.write(bytes([self.buff & 0xff]))
        self.count += 1
        self.hash.update(bytes([self.buff & 0xff]))


class FileDecompressor:
    def __init__(self, input_descriptor, output_descriptor,
                 count, max_code_size=16):
        self.strings = {i: bytes([i]) for i in range(256)}
        self.code_size = 9
        self.max_code = 2 ** max_code_size
        self.in_d = input_descriptor
        self.out_d = output_descriptor
        self.buff = 0
        self.available_bits = 0
        self.next_code = 256
        self.code = 0
        self.hash = hashlib.md5()
        self.count = count
        self.eof = False

    def decompress(self):
        previous_string = b''
        while True:
            self.update_code()

            if self.eof:
                if self.code != 0:
                    self.out_d.write(self.strings[self.code])
                return self.hash.digest()

            if self.code not in self.strings:
                self.strings[self.code] = \
                    previous_string + bytes([previous_string[0]])

            self.out_d.write(self.strings[self.code])

            if len(previous_string) != 0 and self.next_code < self.max_code:
                self.strings[self.next_code] = \
                    previous_string + bytes([self.strings[self.code][0]])
                self.next_code += 1
                self.code_size = (self.next_code + 1).bit_length()

            previous_string = self.strings[self.code]

    def update_code(self):
        while self.available_bits < self.code_size:
            byte = self.in_d.read(1)
            self.count -= 1
            self.hash.update(byte)
            self.buff |= (byte[0] & 0xff) << self.available_bits
            self.available_bits += 8
            if self.count == 0:
                self.eof = True
                break
        self.code = self.buff & ~(~0 << self.code_size)
        self.buff >>= self.code_size
        self.available_bits -= self.code_size


if __name__ == '__main__':
    pass
