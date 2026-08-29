import streamlit as st
import subprocess
import tempfile
import os

st.set_page_config(
    page_title="Video to GIF Converter",
    page_icon="🎬",
    layout="centered"
)

st.title("🎬 Video to GIF Converter")
st.write("Upload a video and convert it into an animated GIF.")

uploaded_file = st.file_uploader(
    "Choose a video",
    type=["mp4", "mov", "avi", "mkv", "webm"]
)

if uploaded_file:
    st.video(uploaded_file)

    col1, col2 = st.columns(2)

    with col1:
        fps = st.slider(
            "FPS",
            min_value=5,
            max_value=30,
            value=10,
            help="Higher FPS produces smoother GIFs but larger files."
        )

    with col2:
        width = st.slider(
            "GIF Width",
            min_value=240,
            max_value=1280,
            value=640,
            step=40
        )

    start_time = st.number_input(
        "Start time (seconds)",
        min_value=0.0,
        value=0.0,
        step=0.5
    )

    duration = st.number_input(
        "Duration (seconds)",
        min_value=0.5,
        value=5.0,
        step=0.5
    )

    if st.button("🔄 Convert to GIF", type="primary"):

        with tempfile.TemporaryDirectory() as temp_dir:

            input_path = os.path.join(
                temp_dir,
                uploaded_file.name
            )

            output_path = os.path.join(
                temp_dir,
                "converted.gif"
            )

            # Save uploaded video
            with open(input_path, "wb") as f:
                f.write(uploaded_file.getbuffer())

            # FFmpeg command
            command = [
                "ffmpeg",
                "-y",
                "-ss", str(start_time),
                "-t", str(duration),
                "-i", input_path,
                "-vf",
                f"fps={fps},scale={width}:-1:flags=lanczos",
                "-loop", "0",
                output_path
            ]

            try:
                with st.spinner("Converting video to GIF..."):
                    result = subprocess.run(
                        command,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True
                    )

                if result.returncode != 0:
                    st.error("Failed to convert the video.")
                    st.code(result.stderr)
                else:
                    st.success("✅ GIF created successfully!")

                    # Read GIF into memory before temporary directory closes
                    with open(output_path, "rb") as f:
                        gif_data = f.read()

                    st.image(gif_data, caption="Generated GIF")

                    st.download_button(
                        label="⬇️ Download GIF",
                        data=gif_data,
                        file_name="converted.gif",
                        mime="image/gif"
                    )

            except FileNotFoundError:
                st.error(
                    "FFmpeg is not installed or is not available "
                    "in your system PATH."
                )