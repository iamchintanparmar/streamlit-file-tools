# 🔄 File Toolkit

A collection of simple Streamlit apps for converting and compressing files — all done locally in your browser.


Created and developed by **[Chintan Parmar](https://github.com/iamchintanparmar)**.

![Python](https://img.shields.io/badge/Python-3776AB?style=flat&logo=python&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green)


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

### 3. Video to GIF Converter (`video_to_gif.py`)
Convert a video clip into an animated GIF:
- Supports `.mp4`, `.mov`, `.avi`, `.mkv`, `.webm` as input
- Adjustable FPS, output width, start time, and clip duration
- Preview the video before converting, and preview/download the resulting GIF

Requires **FFmpeg** to be installed on your system and available on your PATH (this is a separate system tool, not a Python package):
- **Windows**: download from [ffmpeg.org](https://ffmpeg.org/download.html) and add it to PATH
- **macOS**: `brew install ffmpeg`
- **Linux**: `sudo apt install ffmpeg`

Run it with:
```bash
streamlit run video_to_gif.py
```

## Installation

```bash
git clone https://github.com/iamchintanparmar/Streamlit-file-tools/video_to_gif.git
cd video_to_gif
pip install -r requirements.txt
```

## Requirements

- Python 3.8+
- See `requirements.txt` for all packages
## Author

**Chintan Parmar** — Full-Stack Developer & Creative Technologist

- GitHub: [@iamchintanparmar](https://github.com/iamchintanparmar)
- Portfolio: [iamchintanparmar.github.io](https://iamchintanparmar.github.io)

## License

MIT
