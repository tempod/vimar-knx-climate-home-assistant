"""Rasterizza il marchio nei formati richiesti da Home Assistant."""
import pathlib
import cairosvg
from PIL import Image

# Percorsi calcolati rispetto a questo file: resources/icons -> radice repo.
SRC = pathlib.Path(__file__).resolve().parent
ROOT = SRC.parent.parent
OUT = ROOT / "custom_components" / "vimar_knx_climate" / "brand"
OUT.mkdir(parents=True, exist_ok=True)


def render(svg: pathlib.Path, width: int) -> Image.Image:
    tmp = "/tmp/_r.png"
    cairosvg.svg2png(url=str(svg), write_to=tmp, output_width=width)
    return Image.open(tmp).convert("RGBA")


def trim(img: Image.Image) -> Image.Image:
    """Rimuove lo spazio trasparente: le linee guida chiedono immagini rifilate."""
    box = img.getbbox()
    return img.crop(box) if box else img


def save(img: Image.Image, name: str) -> None:
    path = OUT / name
    img.save(path, "PNG", optimize=True)
    print(f"{name:22} {img.width}x{img.height}  {path.stat().st_size / 1024:5.1f} KB")


for base in ("icon", "dark_icon"):
    master = trim(render(SRC / f"{base}.svg", 2048))
    for name, size in ((f"{base}.png", 256), (f"{base}@2x.png", 512)):
        save(master.resize((size, size), Image.LANCZOS), name)

for base in ("logo", "dark_logo"):
    master = trim(render(SRC / f"{base}.svg", 3072))
    for name, height in ((f"{base}.png", 256), (f"{base}@2x.png", 512)):
        width = round(master.width * height / master.height)
        save(master.resize((width, height), Image.LANCZOS), name)
