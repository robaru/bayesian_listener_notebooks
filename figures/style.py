"""Shared style for all paper figures.

Every fig_*.py script imports from here so that font size, the degree-unit
convention, method colors, and the pt-exact figure sizing are identical
across figures.

Consistent *printed* font size hinges on one thing: the width LaTeX is told
to render a figure at (``\\includegraphics[width=...]``) must equal the
figure's actual size, not an independent ``\\linewidth`` fraction that
rescales it. We use PDF-native "bp" units (1/72 inch == LaTeX's ``bp``
unit) throughout, since that's exactly what matplotlib's PDF backend and
LaTeX's ``\\includegraphics`` both use natively -- no pt/bp rounding drift.

Because `savefig(..., bbox_inches="tight")` crops whitespace, the actual
saved page size is slightly smaller than the nominal figure size we asked
for. `savefig()` below measures the real, post-crop page size from the
written PDF and returns it -- `generate_all.py` collects these into
`figures/output/widths.json`, which is the source of truth for the
`\\includegraphics[width=...bp]` values written into the LaTeX source.
"""
import json
import re
import shutil
import subprocess
import warnings
from pathlib import Path

import matplotlib.pyplot as plt

from notebooks.paths import FIG_DIR

BASE_FONT_PT = 8
DEGREE = "(deg)"

# Column width of the edpsci class (\columnwidth = 87mm), in bp (1/72in).
COLUMN_WIDTH_BP = 87 * 72 / 25.4  # ~246.6 bp

# Okabe-Ito colorblind-safe palette, shared by every figure that plots the
# four interpolation methods so the method -> color mapping matches across
# the paper (e.g. bic_comparison and metrics_actual_vs_synthetic).
METHOD_COLORS = {
    "barumerli2023": "#CC79A7",
    "SH": "#56B4E9",
    "SHMAX": "#E69F00",
    "barycentric": "#009E73",
}
METHOD_ORDER = ["barumerli2023", "SH", "SHMAX", "barycentric"]

FIGURES_DIR = FIG_DIR  # figures/output/ (git-ignored), see paths.py
WIDTHS_MANIFEST = FIGURES_DIR / "widths.json"

_MEDIABOX_RE = re.compile(rb"/MediaBox\s*\[\s*([\d.]+)\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)\s*\]")


def apply_style():
    """Reset matplotlib rcParams to the shared paper style."""
    plt.rcdefaults()
    plt.rcParams.update({
        "font.size": BASE_FONT_PT,
        "axes.titlesize": BASE_FONT_PT,
        "axes.labelsize": BASE_FONT_PT,
        "xtick.labelsize": BASE_FONT_PT,
        "ytick.labelsize": BASE_FONT_PT,
        "legend.fontsize": BASE_FONT_PT,
        "figure.titlesize": BASE_FONT_PT,
        "axes.linewidth": 0.8,
        "xtick.major.width": 0.8,
        "ytick.major.width": 0.8,
        "lines.linewidth": 1.0,
        "lines.markersize": 4,
        "legend.frameon": False,
        "pdf.fonttype": 42,
        "svg.fonttype": "none",
    })


def bp_to_in(width_bp):
    return width_bp / 72.0


def _read_mediabox_bp(pdf_path):
    data = Path(pdf_path).read_bytes()
    matches = _MEDIABOX_RE.findall(data)
    if not matches:
        raise RuntimeError(f"Could not find /MediaBox in {pdf_path}")
    x0, y0, x1, y1 = (float(v) for v in matches[-1])
    return x1 - x0, y1 - y0


def _ink_bbox_bp(pdf_path):
    """Return the actual ink bounding box (x0, y0, x1, y1 in bp) of a PDF.

    matplotlib's ``bbox_inches="tight"`` crops to *artist* extents, but a 3D
    axes reports its whole cube as one artist regardless of where the rendered
    content lands -- so a 3D figure keeps a lot of empty page around the
    visible sphere. Ghostscript's bbox device measures the real rendered ink
    instead, which is what we crop against.
    """
    out = subprocess.run(
        ["gs", "-q", "-dNOPAUSE", "-dBATCH", "-sDEVICE=bbox", str(pdf_path)],
        capture_output=True, text=True, check=True)
    text = out.stdout + out.stderr
    m = re.search(r"%%HiResBoundingBox:\s*([\d.]+)\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)", text)
    if not m:
        raise RuntimeError(f"gs bbox device produced no bounding box for {pdf_path}:\n{text}")
    return tuple(float(v) for v in m.groups())


def crop_pdf(pdf_path, sides=("left", "bottom"), pad_bp=1.5):
    """Trim whitespace from the named `sides` down to the PDF's actual ink.

    Only the requested sides move; the others stay at the current page edge.
    Because a PDF stores glyphs at an absolute bp size, shrinking the page box
    removes margin *without* rescaling anything -- font size and layout are
    untouched. Returns the new (post-crop) page size in bp.
    """
    pdf_path = Path(pdf_path)
    if shutil.which("gs") is None:
        warnings.warn("Ghostscript (gs) not found: skipping ink-based cropping of "
                      f"{pdf_path.name} (the figure is otherwise identical).")
        return _read_mediabox_bp(pdf_path)
    page_w, page_h = _read_mediabox_bp(pdf_path)
    x0, y0, x1, y1 = _ink_bbox_bp(pdf_path)
    left = max(0.0, x0 - pad_bp) if "left" in sides else 0.0
    bottom = max(0.0, y0 - pad_bp) if "bottom" in sides else 0.0
    right = min(page_w, x1 + pad_bp) if "right" in sides else page_w
    top = min(page_h, y1 + pad_bp) if "top" in sides else page_h
    if shutil.which("pdfcrop"):
        subprocess.run(
            ["pdfcrop", "--bbox", f"{left} {bottom} {right} {top}",
             str(pdf_path), str(pdf_path)],
            capture_output=True, text=True, check=True)
    else:
        # Fallback without a TeX installation: set the page box with pypdf
        # (same visible result; the PDF keeps a non-zero box origin).
        from pypdf import PdfReader, PdfWriter
        from pypdf.generic import RectangleObject
        writer = PdfWriter(clone_from=PdfReader(str(pdf_path)))
        for page in writer.pages:
            page.mediabox = RectangleObject([left, bottom, right, top])
            page.cropbox = RectangleObject([left, bottom, right, top])
        with open(pdf_path, "wb") as fh:
            writer.write(fh)
    return _read_mediabox_bp(pdf_path)


def savefig(fig, name, width_bp, height_bp=None, pad_bp=1.5, crop_sides=None):
    """Save `fig` as a vector PDF into figures/output/<name>.pdf.

    `width_bp`/`height_bp` set the nominal figure size before cropping.
    The actual, post-crop page size is measured back from the saved PDF
    and recorded in figures/output/widths.json -- that measured value (not the
    nominal one) is what must be used for
    ``\\includegraphics[width=...bp]`` so 1 source pt == 1 printed pt.

    `crop_sides` (e.g. ``("left", "bottom")``) additionally trims those sides
    down to the real rendered ink via `crop_pdf` -- useful for 3D axes, whose
    ``bbox_inches="tight"`` box is much larger than the visible content. The
    post-crop size is what gets recorded in widths.json.
    """
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    fig.set_size_inches(bp_to_in(width_bp), bp_to_in(height_bp) if height_bp else fig.get_size_inches()[1])

    out_path = FIGURES_DIR / f"{name}.pdf"
    fig.savefig(out_path, format="pdf", bbox_inches="tight",
                pad_inches=pad_bp / 72.0, facecolor="white")

    if crop_sides:
        crop_pdf(out_path, sides=crop_sides, pad_bp=pad_bp)

    actual_w_bp, actual_h_bp = _read_mediabox_bp(out_path)

    manifest = {}
    if WIDTHS_MANIFEST.exists():
        manifest = json.loads(WIDTHS_MANIFEST.read_text())
    manifest[name] = {"width_bp": round(actual_w_bp, 2), "height_bp": round(actual_h_bp, 2)}
    WIDTHS_MANIFEST.write_text(json.dumps(manifest, indent=2, sort_keys=True))

    print(f"  saved {out_path.relative_to(FIGURES_DIR.parent.parent)}  "
          f"({actual_w_bp:.1f}bp x {actual_h_bp:.1f}bp)")
    return out_path
