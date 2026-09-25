"""Read the parts of a Bruker M4 Tornado ``.bcf`` header that RosettaSciIO skips.

RosettaSciIO's Bruker reader maps a subset of the XML header into
``metadata`` / ``original_metadata``. For M4 Tornado files that subset misses
the XRF-specific block (tube, filter, optic, geometry), the per-pixel
measurement times, the map configuration record, and three of the four
camera images. This module reads the raw header from the ``.bcf`` container
and returns those pieces as plain Python objects.

Everything here was worked out from one file (see ``uxrf/NOTES.md``); field
meanings marked "unverified" in the notes are passed through as strings.

    from bcf_extras import read_header_xml, xrf_header, map_description, images, pixel_times
    xml = read_header_xml("map.bcf")
    xrf_header(xml)["TubeType"]        # 'MCBM 50-0.6B Rh'
    map_description(xml)["MapGeometry"]  # '55,42,20,0'
    pixel_times(xml)                     # (ny, nx) array, microseconds
    images(xml)["Mosaic"]                # (H, W, 3) uint8 array
"""

import base64
import codecs
import re

import numpy as np

# XML blocks of interest. Each is a ClassInstance with a Type attribute.
_XRF_BLOCK = r'<ClassInstance Type="TRTXrfHeader">(.*?)</ClassInstance>'
_HW_BLOCK = r'<ClassInstance Type="TRTSpectrumHardwareHeader">(.*?)</ClassInstance>'
_DESC_BLOCK = (
    r'<ClassInstance Type="TRTTextData" Name="OverviewImageDescription">'
    r"(.*?)</ClassInstance>"
)
_IMAGE_BLOCK = (
    r'<ClassInstance Type="TRTImageData"(?: Name="([^"]*)")?>(.*?)</ClassInstance>'
)


def read_header_xml(path) -> str:
    """Return the raw XML header stored in ``EDSDatabase/HeaderData``."""
    from rsciio.bruker._api import SFS_reader

    item = SFS_reader(str(path)).get_file("EDSDatabase/HeaderData")
    raw = item.get_as_BytesIO_string().getvalue()
    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError:
        # Esprit writes single-byte characters such as the µ in "Al 100 µm".
        return raw.decode("cp1252", errors="replace")


def _leaves(block: str) -> dict:
    """Flat ``{tag: text}`` of the simple elements in an XML fragment.

    Repeated tags (the two ``FilterId`` entries) are joined with " | ".
    """
    out = {}
    for m in re.finditer(r"<([A-Za-z][A-Za-z0-9_]*)>([^<]*)</\1>", block):
        key, val = m.group(1), m.group(2).strip()
        out[key] = f"{out[key]} | {val}" if key in out else val
    return out


def xrf_header(xml: str) -> dict:
    """Tube, filter, optic, chamber and geometry settings (``TRTXrfHeader``)."""
    m = re.search(_XRF_BLOCK, xml, flags=re.S)
    if m is None:
        return {}
    d = _leaves(m.group(1))
    # The filter sub-blocks flatten into repeated keys; name them explicitly.
    filters = re.findall(r"<FilterId>([^<]*)</FilterId>", m.group(1))
    if filters:
        d["Filters"] = " | ".join(f.strip() for f in filters)
    return d


def hardware_header(xml: str) -> dict:
    """Pulse-processor settings (``TRTSpectrumHardwareHeader``)."""
    m = re.search(_HW_BLOCK, xml, flags=re.S)
    return _leaves(m.group(1)) if m else {}


def map_description(xml: str) -> dict:
    """The base64 ``OverviewImageDescription`` record as ``{key: value}``.

    Known keys: the role of each stored image (``Default=HiRes`` etc.),
    ``MapStartPosMM``, ``MapRectMM``, ``MapGeometry`` and ``MapTime``.
    """
    m = re.search(_DESC_BLOCK, xml, flags=re.S)
    if m is None:
        return {}
    text = re.search(r"<Text>([A-Za-z0-9+/=\s]+)</Text>", m.group(1))
    if text is None:
        return {}
    decoded = base64.b64decode(text.group(1)).decode("utf-8", errors="replace")
    out = {}
    for line in decoded.splitlines():
        if "=" in line:
            key, val = line.split("=", 1)
            out[key.strip()] = val.strip()
    return out


def _decode_planes(body: str):
    width = int(re.search(r"<Width>(\d+)", body).group(1))
    height = int(re.search(r"<Height>(\d+)", body).group(1))
    dtype = "u" + re.search(r"<ItemSize>(\d+)", body).group(1)
    planes = []
    for m in re.finditer(r"<Plane\d+>(.*?)</Plane\d+>", body, flags=re.S):
        data = re.search(r"<Data>(.*?)</Data>", m.group(1), flags=re.S)
        if data is None:
            continue
        raw = codecs.decode(data.group(1).strip().encode("ascii"), "base64")
        planes.append(np.frombuffer(raw, dtype=dtype).reshape(height, width))
    return planes


def _image_blocks(xml: str):
    for m in re.finditer(_IMAGE_BLOCK, xml, flags=re.S):
        yield m.group(1), m.group(2)


def pixel_times(xml: str):
    """Per-pixel measurement time in microseconds, shape ``(ny, nx)``, or None."""
    for name, body in _image_blocks(xml):
        if name == "PixelTimes":
            planes = _decode_planes(body)
            return planes[0].astype(float) if planes else None
    return None


def images(xml: str) -> dict:
    """All multi-plane camera images as ``{role: (H, W, 3) uint8}``.

    Roles come from the description record (HiRes, LowRes, Overview,
    Mosaic); an image without a role keeps its XML name. Plane order is
    taken as R, G, B, which matched the blue-stained epoxy of the first file.
    """
    roles = map_description(xml)
    out = {}
    for name, body in _image_blocks(xml):
        if name in (None, "PixelTimes", "Counter"):
            continue
        planes = _decode_planes(body)
        if len(planes) == 3:
            out[roles.get(name, name)] = np.dstack(planes)
    return out


def counts_per_second(signal, times_us):
    """Divide a map (or spectrum image) by the per-pixel time in seconds.

    ``signal`` is a HyperSpy signal whose navigation shape matches
    ``times_us`` (``(ny, nx)`` in NumPy order); the result keeps the axes and
    metadata and has ``Signal.quantity`` set to counts per second. This is
    the normalisation Esprit applies when it displays maps, and it removes
    the dim first column and the column stripes caused by stage-speed
    variation.
    """
    seconds = np.asarray(times_us, dtype=float) / 1e6
    if signal.axes_manager.signal_dimension > 0:
        # Broadcast (ny, nx) over the trailing signal axes.
        seconds = seconds.reshape(
            seconds.shape + (1,) * signal.axes_manager.signal_dimension
        )
    out = signal / seconds
    out.metadata.set_item("Signal.quantity", "X-rays (Counts per second)")
    return out
