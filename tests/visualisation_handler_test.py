import cairosvg
from PIL import Image
from io import BytesIO


img_png = cairosvg.svg2png(url="./assets/pin.svg")