import struct


class BmpDump:

    _header = None
    _bmp_pixel_array = None
    _width = 0
    _height = 0
    _bpp = 0
    _color_planes_count = 0
    _pixel_compression = 0
    _raw_bitmap_size = 0
    _print_width = 0
    _print_height = 0
    _colors_in_palette = 0
    _important_colors = 0
    _bytes_per_line = 0
    _line_bytes_padding = 0

    def _chunk_array(self, data, length):
        return (data[0 + i:length + i] for i in range(0, len(data), length))

    def _byte_to_uchar(self, b):
        return struct.unpack("B", b)[0]

    def _byte_to_uint(self, b):
        return struct.unpack("I", b)[0]

    def _byte_to_usint(self, b):
        return struct.unpack("H", b)[0]

    def _open_bmp(self, bmp_raw_data):
        id_field = bmp_raw_data[0:2]
        dib_header_size = self._byte_to_uint(bmp_raw_data[14:18])

        self._width = self._byte_to_uint(bmp_raw_data[18:22])
        self._height = self._byte_to_uint(bmp_raw_data[22:26])
        self._color_planes_count = self._byte_to_usint(bmp_raw_data[26:28])
        self._bpp = self._byte_to_usint(bmp_raw_data[28:30])
        self._pixel_compression = self._byte_to_uint(bmp_raw_data[30:34])
        self._raw_bitmap_size = self._byte_to_uint(bmp_raw_data[34:38])
        self._print_width = self._byte_to_uint(bmp_raw_data[38:42])
        self._print_height = self._byte_to_uint(bmp_raw_data[42:46])
        self._colors_in_palette = self._byte_to_uint(bmp_raw_data[46:50])
        self._important_colors = self._byte_to_uint(bmp_raw_data[50:54])

        pixel_map_offset = self._byte_to_uint(bmp_raw_data[10:14])
        self._bmp_pixel_array = list(bmp_raw_data[pixel_map_offset:])
        self._header = list(bmp_raw_data[0:pixel_map_offset])

        bytes_per_line = self._width * (self._bpp / 8)
        if bytes_per_line % 8 != 0:
            self._line_bytes_padding = int(8 - (bytes_per_line % 8))
        else:
            self._line_bytes_padding = int(0)

        assert id_field == b'BM'
        assert dib_header_size == 40
        assert self._colors_in_palette == 0
        assert self._pixel_compression == 0
        assert self._color_planes_count == 1
        assert self._bpp in [4, 8]

    def __init__(self, bmp_name):
        with open(bmp_name, "rb") as f:
            bmp_raw_data = f.read()

        self._open_bmp(bmp_raw_data)

    def _get_lines(self):
        bytes_per_line = (self._width * (self._bpp / 8)) + self._line_bytes_padding
        return list(self._chunk_array(self._bmp_pixel_array, int(bytes_per_line) ))

    def debug(self):
        print("Bmp Width = " + str(self._width))
        print("Bmp Height = " + str(self._height))
        print("Color planes = " + str(self._color_planes_count))
        print("Bits per pixel = " + str(self._bpp))
        print("Pixel compression = " + str(self._pixel_compression))
        print("Raw bitmap size = " + str(self._raw_bitmap_size))
        print("Print width = " + str(self._print_width))
        print("Print height = " + str(self._print_height))
        print("Colors in palette = " + str(self._colors_in_palette))
        print("Important colors = " + str(self._important_colors))
        print("Bmp pixel array size = " + str(len(self._bmp_pixel_array)))

    def upside_down(self):
        pixel_lines = self._get_lines()
        reversed_lines = reversed(pixel_lines)
        self._bmp_pixel_array = list()

        for line in reversed_lines:
            self._bmp_pixel_array = self._bmp_pixel_array + list(line)

    def _generate_pixel_lut_4bpp(self, flip_lut):
        pixel_lut = {}
        for idx in range(0, pow(2, self._bpp)):
            for jdx in range(0, pow(2, self._bpp)):
                pixel_lut[idx*16 + jdx] = flip_lut[idx] * 16 + flip_lut[jdx]

        return pixel_lut

    def flip_colors(self, flip_lut):
        assert len(flip_lut) == pow(2, self._bpp)

        if self._bpp == 4:
            pixel_lut = self._generate_pixel_lut_4bpp(flip_lut)

        flipped_pixels = list()
        for pixel in self._bmp_pixel_array:
            flipped_pixels.append(pixel_lut[pixel])
        self._bmp_pixel_array = flipped_pixels

    def mirror(self):
        self.upside_down()
        self.reverse()

    def reverse(self):
        reversed_pixels = list()
        pixel_lines = self._get_lines()
        reversed_lines = reversed(pixel_lines)

        for line in reversed_lines:
            if self._line_bytes_padding != 0:
                padding = line[-self._line_bytes_padding:]
                pixels = line[:-self._line_bytes_padding]
            else:
                padding = list()
                pixels = line
            for pixel in reversed(pixels):
                if self._bpp == 8:
                    reversed_pixels.append(pixel)
                elif self._bpp == 4:
                    pixel_low = pixel & 0x0f
                    pixel_high = (pixel >> 4) & 0x0f
                    reversed_pixels.append(pixel_low * 16 + pixel_high)

            reversed_pixels = reversed_pixels + padding

        self._bmp_pixel_array = reversed_pixels

    def dump(self, file_name, add_header=True, use_bytes=False, delimiter=""):
        if add_header:
            data_to_dump = self._header + self._bmp_pixel_array
        else:
            data_to_dump = self._bmp_pixel_array

        if use_bytes:
            with open(file_name, "wb") as f:
                f.write(bytearray(data_to_dump))
        else:
            with open(file_name, "w") as f:
                for data in data_to_dump:
                    f.write(str(data) + delimiter)


reverse_colors = {0: 15,   1: 14,     2: 13,     3: 12,
                  4: 11,   5: 10,     6: 9,      7: 8,
                  8: 7,    9: 6,      10: 5,     11: 4,
                  12: 3,   13: 2,     14: 1,     15: 0}

four_colors ={0: 0,   1: 0,     2: 0,     3: 0,
              4: 5,   5: 5,     6: 5,      7: 5,
              8: 10,    9: 10,  10: 10,     11: 10,
              12: 15,   13: 15, 14: 15,     15: 15}

x = BmpDump("testdata/mirror.bmp")
x.reverse()
x.dump("out/dumpRev.bmp", add_header=True, use_bytes=True, delimiter="")

x = BmpDump("testdata/mirror.bmp")
x.upside_down()
x.dump("out/dumpRot.bmp", add_header=True, use_bytes=True, delimiter="")

x = BmpDump("testdata/mirror.bmp")
x.mirror()
x.dump("out/dumpMirr.bmp", add_header=True, use_bytes=True, delimiter="")

for sel_col in range(16):
    one_color = {0: sel_col, 1: sel_col, 2: sel_col, 3: sel_col,
                 4: sel_col, 5: sel_col, 6: sel_col, 7: sel_col,
                 8: sel_col, 9: sel_col, 10: sel_col, 11: sel_col,
                 12: sel_col, 13: sel_col, 14: sel_col, 15: sel_col}
    x = BmpDump("testdata/mirror.bmp")
    x.flip_colors(one_color)
    file_name = "out/dumpcolor" + str(sel_col) + ".bmp"
    x.dump(file_name, add_header=True, use_bytes=True, delimiter="")
