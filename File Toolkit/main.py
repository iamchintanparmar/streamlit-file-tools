import io
import os
import zipfile
from dataclasses import dataclass

import streamlit as st
from PIL import Image

try:
    import pymupdf  # PyMuPDF
except ImportError:  # pragma: no cover
    import fitz as pymupdf  # older versions expose the module as `fitz`


IMAGE_EXTS = {"jpg", "jpeg", "png", "webp", "bmp", "tif", "tiff"}
OFFICE_MEDIA_PREFIXES = ("word/media/", "ppt/media/", "xl/media/")


def human_size(num_bytes: int) -> str:
    """Return a human-readable file size string."""
    size = float(num_bytes)
    for unit in ("B", "KB", "MB", "GB"):
        if size < 1024 or unit == "GB":
            return f"{size:.1f} {unit}" if unit != "B" else f"{int(size)} {unit}"
        size /= 1024
    return f"{size:.1f} GB"


def compress_standalone_image(
    data: bytes,
    ext: str,
    quality: int = 70,
    max_dimension: int = 1920,
) -> tuple[bytes, str]:
    """
    Compress a standalone image file (uploaded directly by the user).
    Returns (new_bytes, output_extension).
    """
    img = Image.open(io.BytesIO(data))
    img.load()
    ext = ext.lower().lstrip(".")

    if max_dimension and max(img.size) > max_dimension:
        img.thumbnail((max_dimension, max_dimension), Image.LANCZOS)

    out = io.BytesIO()

    if ext in ("jpg", "jpeg"):
        if img.mode in ("RGBA", "P", "LA"):
            img = img.convert("RGB")
        img.save(out, format="JPEG", quality=quality, optimize=True)
        return out.getvalue(), "jpg"

    if ext == "png":
        # PNG is lossless, so "quality" instead controls palette quantization.
        if img.mode not in ("P",):
            quantized = img.convert("RGBA").quantize(
                colors=max(16, min(256, int(quality * 2.7))), method=Image.MEDIANCUT
            )
            quantized.save(out, format="PNG", optimize=True)
        else:
            img.save(out, format="PNG", optimize=True)
        return out.getvalue(), "png"

    if ext == "webp":
        if img.mode == "P":
            img = img.convert("RGBA")
        img.save(out, format="WEBP", quality=quality, method=6)
        return out.getvalue(), "webp"

    if ext == "bmp":
        # BMP has no real compression; convert to PNG to actually save space.
        if img.mode in ("P",):
            img = img.convert("RGB")
        img.save(out, format="PNG", optimize=True)
        return out.getvalue(), "png"

    if ext in ("tif", "tiff"):
        img.save(out, format="TIFF", compression="tiff_deflate")
        return out.getvalue(), "tif"

    # Fallback: just re-save in original format
    img.save(out, format=img.format or "PNG")
    return out.getvalue(), ext


def _compress_embedded_image(data: bytes, ext: str, quality: int, max_dimension: int) -> bytes:
    """Compress an image embedded inside a docx/pptx/xlsx, preserving its format."""
    img = Image.open(io.BytesIO(data))
    img.load()
    orig_format = img.format

    if max_dimension and max(img.size) > max_dimension:
        img.thumbnail((max_dimension, max_dimension), Image.LANCZOS)

    out = io.BytesIO()
    if ext in ("jpg", "jpeg"):
        if img.mode in ("RGBA", "P", "LA"):
            img = img.convert("RGB")
        img.save(out, format="JPEG", quality=quality, optimize=True)
    elif ext == "png":
        img.save(out, format="PNG", optimize=True)
    elif ext == "webp":
        img.save(out, format="WEBP", quality=quality, method=6)
    else:
        img.save(out, format=orig_format or "PNG")
    return out.getvalue()


def compress_office_file(
    data: bytes,
    quality: int = 65,
    max_dimension: int = 1600,
) -> bytes:
    """
    Compress a DOCX / PPTX / XLSX file by recompressing the images stored
    inside the underlying OOXML zip archive. Non-image parts are copied
    through unchanged (just re-zipped at max deflate level).
    """
    zin = zipfile.ZipFile(io.BytesIO(data))
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as zout:
        for item in zin.infolist():
            raw = zin.read(item.filename)
            low = item.filename.lower()
            if low.startswith(OFFICE_MEDIA_PREFIXES):
                ext = low.rsplit(".", 1)[-1]
                if ext in ("jpg", "jpeg", "png", "webp"):
                    try:
                        raw = _compress_embedded_image(raw, ext, quality, max_dimension)
                    except Exception:
                        pass  # keep original bytes if anything goes wrong
            zout.writestr(item, raw)
    return buf.getvalue()


def compress_pdf(
    data: bytes,
    quality: int = 60,
    max_dimension: int = 1600,
) -> bytes:
    """
    Compress a PDF by recompressing embedded raster images as JPEG and
    running MuPDF's stream cleanup / garbage collection.
    """
    doc = pymupdf.open(stream=data, filetype="pdf")

    for page in doc:
        for img_info in page.get_images(full=True):
            xref = img_info[0]
            try:
                base = doc.extract_image(xref)
                image_bytes = base["image"]
                pil_img = Image.open(io.BytesIO(image_bytes))
                pil_img.load()

                if max_dimension and max(pil_img.size) > max_dimension:
                    pil_img.thumbnail((max_dimension, max_dimension), Image.LANCZOS)

                if pil_img.mode in ("RGBA", "P", "LA"):
                    pil_img = pil_img.convert("RGB")

                out = io.BytesIO()
                pil_img.save(out, format="JPEG", quality=quality, optimize=True)
                page.replace_image(xref, stream=out.getvalue())
            except Exception:
                continue  # skip images that can't be safely replaced

    out_buf = io.BytesIO()
    doc.save(out_buf, garbage=4, deflate=True, clean=True)
    doc.close()
    return out_buf.getvalue()

@dataclass
class ResultItem:
    name: str
    original_size: int
    new_size: int
    data: bytes


def process_file(name: str, data: bytes, img_quality: int, img_max_dim: int,
                  doc_quality: int, doc_max_dim: int) -> ResultItem | None:
    ext = name.rsplit(".", 1)[-1].lower() if "." in name else ""

    if ext in IMAGE_EXTS:
        try:
            new_data, new_ext = compress_standalone_image(
                data, ext, quality=img_quality, max_dimension=img_max_dim
            )
        except Exception as e:
            st.error(f"Could not process **{name}**: {e}")
            return None
        base = name.rsplit(".", 1)[0]
        out_name = f"{base}_compressed.{new_ext}"
        return ResultItem(out_name, len(data), len(new_data), new_data)

    if ext == "pdf":
        try:
            new_data = compress_pdf(data, quality=doc_quality, max_dimension=doc_max_dim)
        except Exception as e:
            st.error(f"Could not process **{name}**: {e}")
            return None
        base = name.rsplit(".", 1)[0]
        return ResultItem(f"{base}_compressed.pdf", len(data), len(new_data), new_data)

    if ext in ("docx", "pptx", "xlsx"):
        try:
            new_data = compress_office_file(data, quality=doc_quality, max_dimension=doc_max_dim)
        except Exception as e:
            st.error(f"Could not process **{name}**: {e}")
            return None
        base = name.rsplit(".", 1)[0]
        return ResultItem(f"{base}_compressed.{ext}", len(data), len(new_data), new_data)

    st.warning(f"Skipping **{name}** — unsupported file type `.{ext}`")
    return None


def main():
    st.set_page_config(page_title="File Size Reducer", page_icon="🗜️", layout="wide")

    st.title("🗜️ File Size Reducer")
    st.caption(
        "Shrink images (JPG, PNG, WEBP, BMP, TIFF) and documents "
        "(PDF, DOCX, PPTX, XLSX) — all processing happens locally in this app."
    )

    with st.sidebar:
        st.header("Settings")

        st.subheader("Images")
        img_quality = st.slider("Image quality", 10, 95, 70, help="Lower = smaller file, more quality loss.")
        img_max_dim = st.slider("Max image dimension (px)", 400, 4000, 1920, step=100,
                                 help="Longest side is resized down to this if larger.")

        st.subheader("Documents (PDF / DOCX / PPTX / XLSX)")
        doc_quality = st.slider("Embedded image quality", 10, 95, 60)
        doc_max_dim = st.slider("Max embedded image dimension (px)", 400, 3000, 1600, step=100)

        st.divider()
        st.caption(
            "PDFs are compressed by recompressing embedded images and cleaning "
            "up redundant stream data. DOCX/PPTX/XLSX are compressed by "
            "recompressing the images stored inside the file — text and "
            "formatting are left untouched."
        )

    uploaded_files = st.file_uploader(
        "Upload one or more files",
        type=["jpg", "jpeg", "png", "webp", "bmp", "tif", "tiff", "pdf", "docx", "pptx", "xlsx"],
        accept_multiple_files=True,
    )

    if not uploaded_files:
        st.info("Upload images or documents above to get started.")
        return

    if st.button("🚀 Compress files", type="primary"):
        results: list[ResultItem] = []
        progress = st.progress(0.0)
        for i, f in enumerate(uploaded_files):
            data = f.read()
            item = process_file(f.name, data, img_quality, img_max_dim, doc_quality, doc_max_dim)
            if item:
                results.append(item)
            progress.progress((i + 1) / len(uploaded_files))
        progress.empty()

        if not results:
            st.error("No files were successfully compressed.")
            return

        st.success(f"Compressed {len(results)} file(s).")

        total_before = sum(r.original_size for r in results)
        total_after = sum(r.new_size for r in results)
        total_saved_pct = (1 - total_after / total_before) * 100 if total_before else 0

        c1, c2, c3 = st.columns(3)
        c1.metric("Total before", human_size(total_before))
        c2.metric("Total after", human_size(total_after))
        c3.metric("Total saved", f"{total_saved_pct:.1f}%")

        st.divider()

        for r in results:
            saved_pct = (1 - r.new_size / r.original_size) * 100 if r.original_size else 0
            col1, col2 = st.columns([3, 1])
            with col1:
                st.write(f"**{r.name}**")
                st.caption(
                    f"{human_size(r.original_size)} → {human_size(r.new_size)} "
                    f"({saved_pct:.1f}% smaller)" if saved_pct >= 0 else
                    f"{human_size(r.original_size)} → {human_size(r.new_size)} (no reduction)"
                )
                st.progress(min(max(r.new_size / r.original_size, 0.0), 1.0))
            with col2:
                st.download_button(
                    "⬇️ Download",
                    data=r.data,
                    file_name=r.name,
                    key=f"dl_{r.name}",
                    use_container_width=True,
                )

        if len(results) > 1:
            zip_buf = io.BytesIO()
            with zipfile.ZipFile(zip_buf, "w", zipfile.ZIP_DEFLATED) as zf:
                for r in results:
                    zf.writestr(r.name, r.data)
            st.divider()
            st.download_button(
                "⬇️ Download all as ZIP",
                data=zip_buf.getvalue(),
                file_name="compressed_files.zip",
                mime="application/zip",
                use_container_width=True,
            )


if __name__ == "__main__":
    main()