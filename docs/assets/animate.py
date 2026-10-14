"""Export the cover's small decorative motions to a self-contained GIF."""
from copy import deepcopy
import ctypes as C
import ctypes.util
from io import BytesIO
import math
from pathlib import Path
import xml.etree.ElementTree as ET


def native_rasterizer():
    """Use existing librsvg/cairo installations when CairoSVG is unavailable."""
    paths = {name: ctypes.util.find_library(name) for name in ('rsvg-2', 'cairo', 'gobject-2.0')}
    if not all(paths.values()):
        raise SystemExit('GIF export needs CairoSVG or system librsvg/cairo libraries.')
    rsvg, cairo, gobject = (C.CDLL(paths[name]) for name in ('rsvg-2', 'cairo', 'gobject-2.0'))
    pointer = C.c_void_p

    def bind(library, name, returns, arguments):
        function = getattr(library, name)
        function.restype, function.argtypes = returns, arguments
        return function

    load = bind(rsvg, 'rsvg_handle_new_from_data', pointer, [C.c_char_p, C.c_size_t, pointer])
    render = bind(rsvg, 'rsvg_handle_render_cairo', C.c_int, [pointer, pointer])
    surface_new = bind(cairo, 'cairo_image_surface_create', pointer, [C.c_int, C.c_int, C.c_int])
    context_new = bind(cairo, 'cairo_create', pointer, [pointer])
    scale = bind(cairo, 'cairo_scale', None, [pointer, C.c_double, C.c_double])
    callback_type = C.CFUNCTYPE(C.c_int, pointer, pointer, C.c_uint)
    write = bind(cairo, 'cairo_surface_write_to_png_stream', C.c_int, [pointer, callback_type, pointer])
    context_free = bind(cairo, 'cairo_destroy', None, [pointer])
    surface_free = bind(cairo, 'cairo_surface_destroy', None, [pointer])
    unref = bind(gobject, 'g_object_unref', None, [pointer])

    def svg2png(*, bytestring, output_width, output_height):
        svg = ET.fromstring(bytestring)
        source_width, source_height = float(svg.get('width')), float(svg.get('height'))
        handle = load(bytestring, len(bytestring), None)
        if not handle:
            raise RuntimeError('librsvg could not read the cover SVG')
        surface = surface_new(0, output_width, output_height)
        context = context_new(surface)
        chunks = []

        @callback_type
        def write_chunk(closure, data, length):
            chunks.append(C.string_at(data, length))
            return 0

        try:
            scale(context, output_width / source_width, output_height / source_height)
            if not render(handle, context) or write(surface, write_chunk, None) != 0:
                raise RuntimeError('Could not rasterize the cover SVG')
            return b''.join(chunks)
        finally:
            context_free(context)
            surface_free(surface)
            unref(handle)
    return svg2png


def export_gif(source: Path, destination: Path) -> None:
    try:
        from PIL import Image
    except ImportError as error:
        raise SystemExit('GIF export needs Pillow: python -m pip install Pillow') from error
    try:
        from cairosvg import svg2png
    except ImportError:
        svg2png = native_rasterizer()
    root = ET.parse(source).getroot()
    frames = []
    count = 48
    for index in range(count):
        frame = deepcopy(root)
        angle = index * 2 * math.pi / count
        for element in frame.iter():
            motion = element.get('data-motion')
            if motion == 'float':
                offset = 5 * math.sin(angle + float(element.get('data-phase', 0)))
                element.set('transform', f'translate(0 {offset:.3f}) ' + element.get('transform', ''))
            elif motion == 'spark':
                element.set('opacity', f'{.8 + .2 * math.sin(angle):.3f}')
            if element.get('class') == 'waving-arm':
                rotation = 13 * math.sin(angle * 2)
                element.set('transform', f'rotate({rotation:.3f} 56 46)')
        png = svg2png(bytestring=ET.tostring(frame), output_width=1080, output_height=420)
        with Image.open(BytesIO(png)) as rendered:
            background = Image.new('RGB', rendered.size, '#FFF8ED')
            if rendered.mode == 'RGBA':
                background.paste(rendered, mask=rendered.getchannel('A'))
            else:
                background.paste(rendered)
        if not frames:
            palette = background.quantize(colors=256)
        frames.append(background.quantize(palette=palette, dither=Image.Dither.NONE))
    durations = [120 if index % 2 == 0 else 130 for index in range(count)]
    frames[0].save(destination, save_all=True, append_images=frames[1:], duration=durations,
                   loop=0, optimize=True, disposal=1)
    print(f'{destination.name}: {len(frames)} frames, 6-second loop, {destination.stat().st_size:,} bytes')
