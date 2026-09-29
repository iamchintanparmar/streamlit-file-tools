import io
import json
import os

import pandas as pd
import streamlit as st
from PIL import Image
from bs4 import BeautifulSoup
from docx import Document
from PyPDF2 import PdfReader
from reportlab.pdfgen import canvas

st.set_page_config(
    page_title="Universal File Converter",
    page_icon="🔄",
    layout="wide"
)

st.title("🔄 Universal File Converter")


def ext(filename):
    """Get the lowercase file extension without the dot (e.g. 'report.PDF' -> 'pdf')."""
    return os.path.splitext(filename)[1].lower().replace(".", "")


def text_to_pdf(text):
    """Turn plain text into a simple PDF, one line of text per line on the page."""
    output = io.BytesIO()
    pdf = canvas.Canvas(output)
    y = 800  # start near the top of the page

    for line in text.splitlines():
        # Out of room on this page, so start a new one
        if y < 50:
            pdf.showPage()
            y = 800
        # Long lines get cut at 120 chars so they don't run off the page
        pdf.drawString(50, y, line[:120])
        y -= 15

    pdf.save()
    output.seek(0)
    return output.read()


def df_to_xlsx(df):
    """Write a DataFrame to an Excel file in memory and return the bytes."""
    output = io.BytesIO()

    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False)

    output.seek(0)
    return output.read()


def df_to_csv(df):
    """DataFrame -> CSV bytes."""
    return df.to_csv(index=False).encode("utf-8")


def df_to_json(df):
    """DataFrame -> pretty JSON (list of records), keeping non-English characters readable."""
    return df.to_json(
        orient="records",
        indent=4,
        force_ascii=False
    ).encode("utf-8")


def image_convert(data, output_format):
    """Convert an image to another format and return the new file's bytes."""
    image = Image.open(io.BytesIO(data))
    output = io.BytesIO()

    if output_format == "jpg":
        # JPEG doesn't support transparency, so put the image on a white background
        if image.mode in ("RGBA", "LA"):
            background = Image.new("RGB", image.size, "white")
            background.paste(
                image,
                mask=image.getchannel("A")
            )
            image = background
        else:
            image = image.convert("RGB")

        # Pillow calls it "JPEG", not "JPG"
        output_format = "jpeg"

    image.save(output, format=output_format.upper())
    output.seek(0)

    return output.read()


# ---------------------------------------------------------------------------
# UI
# ---------------------------------------------------------------------------
uploaded = st.file_uploader(
    "Upload a file",
    type=None  # accept anything, we check the extension ourselves below
)

if uploaded:

    filename = uploaded.name
    input_format = ext(filename)
    data = uploaded.read()

    st.success(f"Uploaded: {filename}")

    # What each input type can be converted into
    formats = {
        "txt": ["pdf", "html", "json"],
        "csv": ["xlsx", "json", "txt"],
        "xlsx": ["csv", "json", "txt"],
        "xls": ["csv", "json", "txt"],
        "json": ["csv", "xlsx", "txt"],
        "docx": ["txt", "pdf"],
        "pdf": ["txt"],
        "html": ["txt", "html"],
        "png": ["jpg", "webp", "bmp", "tiff"],
        "jpg": ["png", "webp", "bmp", "tiff"],
        "jpeg": ["png", "webp", "bmp", "tiff"],
        "webp": ["png", "jpg", "bmp", "tiff"],
        "bmp": ["png", "jpg", "webp", "tiff"],
        "tiff": ["png", "jpg", "webp", "bmp"]
    }

    # Stop early if we don't know how to handle this file type
    if input_format not in formats:
        st.error("This file format is not supported yet.")
        st.stop()

    output_format = st.selectbox(
        "Convert to",
        formats[input_format]
    )

    if st.button("🔄 Convert", type="primary"):

        try:
            result = None

            # ---- Plain text ----
            if input_format in ["txt", "text"]:
                # errors="ignore" so odd characters don't crash the decode
                text = data.decode("utf-8", errors="ignore")

                if output_format == "pdf":
                    result = text_to_pdf(text)

                elif output_format == "html":
                    # Wrap the text in <pre> so line breaks and spacing are kept
                    result = f"""
<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<title>Converted File</title>
</head>
<body>
<pre>{text}</pre>
</body>
</html>
""".encode("utf-8")

                elif output_format == "json":
                    result = json.dumps(
                        {
                            "filename": filename,
                            "content": text
                        },
                        indent=4,
                        ensure_ascii=False
                    ).encode("utf-8")

            # ---- CSV ----
            elif input_format == "csv":
                df = pd.read_csv(io.BytesIO(data))

                if output_format == "xlsx":
                    result = df_to_xlsx(df)
                elif output_format == "json":
                    result = df_to_json(df)
                elif output_format == "txt":
                    result = df.to_string(index=False).encode("utf-8")

            # ---- Excel ----
            elif input_format in ["xlsx", "xls"]:
                df = pd.read_excel(io.BytesIO(data))

                if output_format == "csv":
                    result = df_to_csv(df)
                elif output_format == "json":
                    result = df_to_json(df)
                elif output_format == "txt":
                    result = df.to_string(index=False).encode("utf-8")

            # ---- JSON ----
            elif input_format == "json":
                obj = json.loads(
                    data.decode("utf-8", errors="ignore")
                )

                # Flatten nested JSON into table columns
                df = pd.json_normalize(obj)

                if output_format == "csv":
                    result = df_to_csv(df)
                elif output_format == "xlsx":
                    result = df_to_xlsx(df)
                elif output_format == "txt":
                    # For txt we just re-dump the original JSON, nicely indented
                    result = json.dumps(
                        obj,
                        indent=4,
                        ensure_ascii=False
                    ).encode("utf-8")

            # ---- Word ----
            elif input_format == "docx":
                document = Document(io.BytesIO(data))
                # Only paragraph text is pulled out (tables, images, etc. are ignored)
                text = "\n".join(
                    paragraph.text
                    for paragraph in document.paragraphs
                )

                if output_format == "txt":
                    result = text.encode("utf-8")
                elif output_format == "pdf":
                    result = text_to_pdf(text)

            # ---- PDF ----
            elif input_format == "pdf":
                reader = PdfReader(io.BytesIO(data))
                # extract_text() can return None on image-only pages, so fall back to ""
                text = "\n".join(
                    page.extract_text() or ""
                    for page in reader.pages
                )

                # txt is the only option for PDFs
                result = text.encode("utf-8")

            # ---- HTML ----
            elif input_format == "html":
                html = data.decode("utf-8", errors="ignore")

                if output_format == "html":
                    # Nothing to convert, hand back the original file
                    result = data
                elif output_format == "txt":
                    # Strip the tags and keep just the visible text
                    soup = BeautifulSoup(html, "html.parser")
                    result = soup.get_text(
                        separator="\n"
                    ).encode("utf-8")

            # ---- Images ----
            elif input_format in [
                "png",
                "jpg",
                "jpeg",
                "webp",
                "bmp",
                "tiff"
            ]:
                result = image_convert(
                    data,
                    output_format
                )

            # Only show the download button if a conversion actually produced something
            if result:
                output_filename = (
                    os.path.splitext(filename)[0]
                    + "."
                    + output_format
                )

                st.success("Conversion completed!")

                st.download_button(
                    "⬇️ Download",
                    result,
                    file_name=output_filename,
                    mime="application/octet-stream"
                )

        except Exception as e:
            st.error(f"Conversion failed: {e}")
