"""
This code is based on examples kindly created, documented, and shared by Adafruit:

This is for use on (Linux) computers that are using CPython with
Adafruit Blinka to support CircuitPython libraries. CircuitPython does
not support PIL/pillow (python imaging library)!
"""

import board
import sys, getopt
import digitalio
from PIL import Image, ImageDraw, ImageFont
import adafruit_ssd1306

argv = sys.argv[1:]

textLine1 = ''
textLine2 = ''
textLine3 = ''
textSize = ''

try:
    opts, args = getopt.getopt(argv, "ha:b:c:s:", ["firstLine=", "secondLine=", "thirdLine=", "textSize="])
except getopt.GetoptError:
    print('printToOLED.py -a <firstline> -b <secondline> -c <thirdline> -s <textsize>')
    sys.exit(2)

for opt, arg in opts:
    if opt == '-h':
        print('printToOLED.py -a <firstline> -b <secondline> -c <thirdline> -s <textsize>')
        sys.exit()
    elif opt in ("-a", "--firstLine"):
        textLine1 = arg
    elif opt in ("-b", "--secondLine"):
        textLine2 = arg
    elif opt in ("-c", "--thirdLine"):
        textLine3 = arg
    elif opt in ("-s", "--textSize"):
        textSize = int(arg)

oled_reset = None

WIDTH = 128
HEIGHT = 64
BORDER = 5

i2c = board.I2C()
oled = adafruit_ssd1306.SSD1306_I2C(128, 64, i2c, addr=0x3C, reset=None)

oled.fill(0)
oled.show()

image = Image.new("1", (oled.width, oled.height))
draw = ImageDraw.Draw(image)

font_path = "/home/pi/SmartChess/RaspberryPiCode/WorkSans-Medium.ttf"
font = ImageFont.truetype(font_path, textSize)

def draw_text_centered(text, y):
    (font_width, font_height) = font.getsize(text)
    draw.text(
        (oled.width // 2 - font_width // 2, y),
        text,
        font=font,
        fill=255,
    )

draw_text_centered(textLine1, 0)
draw_text_centered(textLine2, 20)
draw_text_centered(textLine3, 40)

oled.image(image)
oled.show()



