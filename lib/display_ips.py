# Mini Driver para display IPS 80x160
# (C) 2023, Daniel Quadros
#
# Baseado em:
#   https://github.com/peterhinch/micropython-nano-gui
#   https://github.com/adafruit/Adafruit-ST7735-Library

from time import sleep_ms
from uctypes import bytearray_at, addressof
import framebuf

# Paleta com cores de frente e fundo
class BoolPalette(framebuf.FrameBuffer):

    def __init__(self, mode):
        buf = bytearray(4)
        super().__init__(buf, 2, 1, mode)
    
    def fg(self, color):  # Set foreground color
        self.pixel(1, 0, color)

    def bg(self, color):
        self.pixel(0, 0, color)


class DISPLAY_IPS(framebuf.FrameBuffer):
    
    # Converte cor (r, g, b) para um valor de 16 bits
    # rrrrrggggggbbbbb
    @staticmethod
    def rgb(r, g, b):
        x = ((r & 0xf8) << 8) | ((g & 0xfc) << 3) | (b >> 3)
        return ((x & 0xFF) << 8) | (x >> 8)

    # Criacao do objetp
    def __init__(self, spi, cs, dc, rst, height=128, width=160):
        self._spi = spi
        self._rst = rst
        self._dc = dc
        self._cs = cs
        self.height = height
        self.width = width
        self.mode = framebuf.RGB565
        self.palette = BoolPalette(self.mode)
        buf = bytearray(height * width * 2)
        self._mvb = memoryview(buf)
        super().__init__(buf, width, height, self.mode)
        self._init()
        self.show()

    # Hardware reset
    def _hwreset(self):
        self._dc(0)
        self._rst(1)
        sleep_ms(1)
        self._rst(0)
        sleep_ms(1)
        self._rst(1)
        sleep_ms(1)

    # Write a command, a bytes instance (in practice 1 byte).
    def _wcmd(self, buf):
        self._dc(0)
        self._cs(0)
        self._spi.write(buf)
        self._cs(1)

    # Write a command followed by a data arg.
    def _wcd(self, c, d):
        self._dc(0)
        self._cs(0)
        self._spi.write(c)
        self._cs(1)
        self._dc(1)
        self._cs(0)
        self._spi.write(d)
        self._cs(1)

    # Inicia o controlador
    def _init(self):
        self._hwreset()  # Hardware reset. Blocks 3ms
        cmd = self._wcmd
        wcd = self._wcd
        cmd(b'\x01')  # SW reset datasheet specifies > 120ms
        sleep_ms(150)
        cmd(b'\x11')  # SLPOUT
        sleep_ms(256)  # Adafruit delay (datsheet 120ms)
        wcd(b'\xb1', b'\x01\x2C\x2D')  # FRMCTRL1
        wcd(b'\xb2', b'\x01\x2C\x2D')  # FRMCTRL2
        wcd(b'\xb3', b'\x01\x2C\x2D\x01\x2C\x2D')  # FRMCTRL3
        wcd(b'\xb4', b'\x07')  # INVCTR line inversion

        wcd(b'\xc0', b'\xa2\x02\x84')  # PWCTR1 GVDD = 4.7V, 1.0uA
        wcd(b'\xc1', b'\xc5')  # PWCTR2 VGH=14.7V, VGL=-7.35V
        wcd(b'\xc2', b'\x0a\x00')  # PWCTR3 Opamp current small, Boost frequency
        wcd(b'\xc3', b'\x8a\x2a')  # PWCTR4
        wcd(b'\xc4', b'\x8a\xee')  # PWCTR5 
        wcd(b'\xc5', b'\x0e')  # VMCTR1 VCOMH = 4V, VOML = -1.1V  NOTE I make VCOM == -0.775V

        cmd(b'\x20') # INVOFF
        wcd(b'\x36', b'\x68')  # MADCTL
        wcd(b'\x3a', b'\x05')  # COLMOD 16 bit
        
        wcd(b'\x2a', b'\x00\x00\x00\x9F')  # CASET
        wcd(b'\x2b', b'\x00\x18\x00\x67')  # RASET
        
        wcd(b'\xe0', b'\x02\x1c\x07\x12\x37\x32\x29\x2d\x29\x25\x2B\x39\x00\x01\x03\x10')  # GMCTRP1 Gamma
        wcd(b'\xe1', b'\x03\x1d\x07\x06\x2E\x2C\x29\x2D\x2E\x2E\x37\x3F\x00\x00\x02\x10')  # GMCTRN1

        cmd(b'\x13')  # NORON
        sleep_ms(10)
        cmd(b'\x29')  # DISPON
        sleep_ms(100)

    # Envia a imagem da tela para o display
    def show(self):  
        self._dc(0)
        self._cs(0)
        self._spi.write(b'\x2c')  # RAMWR
        self._dc(1)
        self._spi.write(self._mvb)
        self._cs(1)
        
    # Escreve um caracter, retorna largura
    def _printc(self, x, y, c, fonte):
        glyph, char_height, char_width = fonte.get_ch(c)
        if glyph is None:
            return  # nada a escrever
        buf = bytearray_at(addressof(glyph), len(glyph))
        fbc = framebuf.FrameBuffer(buf, char_width, char_height, self.map)
        self.blit(fbc, x, y, -1, self.palette)
        return char_width
        
    # Escreve texto
    def print(self, x, y, texto, fonte, frente, fundo):
        self.map = framebuf.MONO_HMSB if fonte.reverse() else framebuf.MONO_HLSB
        palette = self.palette
        palette.bg(fundo)
        palette.fg(frente)
        for c in texto:
            x = x + self._printc (x, y, c, fonte)
        

# Teste simples
if __name__ == '__main__':
    from machine import Pin, SPI
    import gc
    import fonts.freesans20 as freesans20
    import fonts.weather_font as wfont

    pdc = Pin(14, Pin.OUT, value=0)
    prst = Pin(13, Pin.OUT, value=1)
    pcs = Pin(9, Pin.OUT, value=1)
    gc.collect()  # Precaution before instantiating framebuf
    spi = SPI(1, sck=Pin(10), mosi=Pin(11), baudrate=1_000_000)
    disp = DISPLAY_IPS(spi, pcs, pdc, prst, 80, 160)
    WHITE = disp.rgb(255,255,255)
    GRAY = disp.rgb(127,127,127)
    BLACK = disp.rgb(0,0,0)
    BLUE = disp.rgb(0,0,255)
    disp.fill(BLUE)
    disp.print(80, 10, "12:34", freesans20, WHITE, BLUE)
    disp.print(80, 40, "34.5 C", freesans20, GRAY, BLUE)
    disp.print(20, 4, "\x0d", wfont, WHITE, BLUE)
    disp.show()
