import cairosvg
from PIL import Image
from io import BytesIO
import xarray as xr

img_png = cairosvg.svg2png(url="./assets/pin.svg", scale=2.0)
icon_img = Image.open(BytesIO(img_png))


ds = xr.open_dataset("ERA5.netcdf")

temp = ds.isel(latitude=30, longitude=30)
temp.plot()