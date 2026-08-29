# 🔄 File Toolkit

A collection of simple Streamlit apps for converting and compressing files — all done locally in your browser.

## Apps

### 1. Universal File Converter (`formate_to_formate.py`)
Convert files between common formats:
- **Text**: `.txt` → PDF, HTML, JSON
- **Spreadsheets**: `.csv`, `.xlsx`, `.xls`, `.json` → converted between each other and `.txt`
- **Documents**: `.docx` → TXT, PDF | `.pdf` → TXT | `.html` → TXT, HTML
- **Images**: `.png`, `.jpg`, `.jpeg`, `.webp`, `.bmp`, `.tiff` → converted between each other

Run it with:
```bash
streamlit run formate_to_formate.py
```

### 2. File Size Reducer (`size_reducer.py`)
Shrink the file size of images and documents while keeping them usable:
- **Images**: JPG, PNG, WEBP, BMP, TIFF — resized and recompressed with adjustable quality
- **PDF**: embedded images recompressed, redundant data cleaned up
- **DOCX / PPTX / XLSX**: embedded images recompressed in place; text and formatting untouched

Supports batch upload, before/after size comparison, and a "download all as ZIP" option.

Run it with:
```bash
streamlit run size_reducer.py
```

## Installation

```bash
git clone https://github.com/your-username/your-repo-name.git
cd your-repo-name
pip install -r requirements.txt
```

## Requirements

- Python 3.8+
- See `requirements.txt` for all packages

## License

MIT