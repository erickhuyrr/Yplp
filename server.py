from fastapi import FastAPI, Query
from fastapi.responses import FileResponse, JSONResponse
import yt_dlp
import tempfile
import os

app = FastAPI(title="yt-dlp API")

@app.get("/")
def root():
    return {"message": "yt-dlp API is running"}

@app.get("/info")
def get_info(
    url: str = Query(..., description="Video/Audio URL")
):
    """
    Get all video and audio formats for a URL.
    """
    try:
        ydl_opts = {
            "quiet": True,
            "skip_download": True,  # Don't download yet
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)

        video_formats = []
        audio_formats = []

        for f in info.get("formats", []):
            fmt_info = {
                "format_id": f.get("format_id"),
                "ext": f.get("ext"),
                "resolution": f.get("resolution") or f.get("height"),
                "fps": f.get("fps"),
                "abr": f.get("abr"),
                "filesize": f.get("filesize"),
                "url": f.get("url")
            }

            # Categorize
            if f.get("vcodec") != "none" and f.get("acodec") == "none":
                video_formats.append(fmt_info)
            elif f.get("vcodec") == "none" and f.get("acodec") != "none":
                audio_formats.append(fmt_info)
            elif f.get("vcodec") != "none" and f.get("acodec") != "none":
                video_formats.append(fmt_info)

        return JSONResponse(
            content={
                "title": info.get("title"),
                "uploader": info.get("uploader"),
                "duration": info.get("duration"),
                "video_formats": video_formats,
                "audio_formats": audio_formats
            }
        )

    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})


@app.get("/download")
def download(
    url: str = Query(..., description="Video/Audio URL"),
    format_id: str = Query(..., description="format_id from /info")
):
    """
    Download a file by format_id
    """
    try:
        temp_dir = tempfile.mkdtemp()
        output_template = os.path.join(temp_dir, "%(id)s.%(ext)s")

        ydl_opts = {
            "outtmpl": output_template,
            "format": format_id,
            "noplaylist": True,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)

        # Get downloaded file
        downloaded_file = None
        for file in os.listdir(temp_dir):
            downloaded_file = os.path.join(temp_dir, file)
            break

        if not downloaded_file or not os.path.exists(downloaded_file):
            return JSONResponse(status_code=500, content={"error": "Download failed"})

        filename = os.path.basename(downloaded_file)
        return FileResponse(downloaded_file, filename=filename, media_type="application/octet-stream")

    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})
