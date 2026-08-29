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
    return os.path.splitext(filename)[1].lower().replace(".", "")

def text_to_pdf(text):
    output = io.BytesIO()
    pdf = canvas.Canvas(output)
    y = 800

    for line in text.splitlines():
        if y < 50:
            pdf.showPage()
            y = 800
        pdf.drawString(50, y, line[:120])
        y -= 15

    pdf.save()
    output.seek(0)
    return output.read()

def df_to_xlsx(df):
    output = io.BytesIO()

    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False)

    output.seek(0)
    return output.read()

def df_to_csv(df):
    return df.to_csv(index=False).encode("utf-8")

def df_to_json(df):
    return df.to_json(
        orient="records",
        indent=4,
        force_ascii=False
    ).encode("utf-8")

def image_convert(data, output_format):
    image = Image.open(io.BytesIO(data))
    output = io.BytesIO()

    if output_format == "jpg":
        if image.mode in ("RGBA", "LA"):
            background = Image.new("RGB", image.size, "white")
            background.paste(
                image,
                mask=image.getchannel("A")
            )
            image = background
        else:
            image = image.convert("RGB")

        output_format = "jpeg"

    image.save(output, format=output_format.upper())
    output.seek(0)

    return output.read()

uploaded = st.file_uploader(
    "Upload a file",
    type=None
)

if uploaded:

    filename = uploaded.name
    input_format = ext(filename)
    data = uploaded.read()

    st.success(f"Uploaded: {filename}")

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

            if input_format in ["txt", "text"]:
                text = data.decode("utf-8", errors="ignore")

                if output_format == "pdf":
                    result = text_to_pdf(text)

                elif output_format == "html":
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

            elif input_format == "csv":
                df = pd.read_csv(io.BytesIO(data))

                if output_format == "xlsx":
                    result = df_to_xlsx(df)
                elif output_format == "json":
                    result = df_to_json(df)
                elif output_format == "txt":
                    result = df.to_string(index=False).encode("utf-8")

            elif input_format in ["xlsx", "xls"]:
                df = pd.read_excel(io.BytesIO(data))

                if output_format == "csv":
                    result = df_to_csv(df)
                elif output_format == "json":
                    result = df_to_json(df)
                elif output_format == "txt":
                    result = df.to_string(index=False).encode("utf-8")

            elif input_format == "json":
                obj = json.loads(
                    data.decode("utf-8", errors="ignore")
                )

                df = pd.json_normalize(obj)

                if output_format == "csv":
                    result = df_to_csv(df)
                elif output_format == "xlsx":
                    result = df_to_xlsx(df)
                elif output_format == "txt":
                    result = json.dumps(
                        obj,
                        indent=4,
                        ensure_ascii=False
                    ).encode("utf-8")

            elif input_format == "docx":
                document = Document(io.BytesIO(data))
                text = "\n".join(
                    paragraph.text
                    for paragraph in document.paragraphs
                )

                if output_format == "txt":
                    result = text.encode("utf-8")
                elif output_format == "pdf":
                    result = text_to_pdf(text)

            elif input_format == "pdf":
                reader = PdfReader(io.BytesIO(data))
                text = "\n".join(
                    page.extract_text() or ""
                    for page in reader.pages
                )

                result = text.encode("utf-8")

            elif input_format == "html":
                html = data.decode("utf-8", errors="ignore")

                if output_format == "html":
                    result = data
                elif output_format == "txt":
                    soup = BeautifulSoup(html, "html.parser")
                    result = soup.get_text(
                        separator="\n"
                    ).encode("utf-8")

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