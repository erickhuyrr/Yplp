from fastapi import FastAPI, Query
from fastapi.responses import FileResponse, JSONResponse
import yt_dlp
import tempfile
import os

app = FastAPI(title="yt-dlp API with browser cookies support")

@app.get("/")
def root():
    return {"message": "yt-dlp API is running"}

@app.get("/download")
def download(
    url: str = Query(..., description="Video/Audio URL"),
    format: str = Query("mp4", description="mp4 for video, mp3 for audio")
):
    try:
        # Create temporary directory
        temp_dir = tempfile.mkdtemp()

        # Safe filename template
        output_template = os.path.join(temp_dir, "%(id)s.%(ext)s")

        # yt-dlp options
        ydl_opts = {
            "outtmpl": output_template,
            "noplaylist": True,
            # Automatic cookies from browser (Chrome default)
            "cookiesfrombrowser": ("chrome", None),  # None uses default path
        }

        # Audio extraction if requested
        if format.lower() == "mp3":
            ydl_opts.update({
                "format": "bestaudio/best",
                "postprocessors": [{
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": "192"
                }]
            })

        # Download video/audio
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)

        # Get downloaded file path
        downloaded_file = None
        for file in os.listdir(temp_dir):
            downloaded_file = os.path.join(temp_dir, file)
            break

        if not downloaded_file or not os.path.exists(downloaded_file):
            return JSONResponse(status_code=500, content={"error": "Download failed"})

        # Return file as response
        filename = os.path.basename(downloaded_file)
        return FileResponse(downloaded_file, filename=filename, media_type="application/octet-stream")

    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})
