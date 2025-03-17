# dummy request
# {
#   "urls": ["https://www.youtube.com/watch?v=picePk8lb48","https://www.youtube.com/watch?v=picePk8lb48"]
# }



from flask import Flask, request, jsonify
from youtube_transcript_api import YouTubeTranscriptApi
import yt_dlp
import re
import ssl
import certifi
import sys
# Fix SSL certificate issue
ssl._create_default_https_context = ssl.create_default_context(cafile=certifi.where())

app = Flask(__name__)

def sanitize_filename(title):
    """Clean filename by removing special characters"""
    if not title:
        return None
    return re.sub(r'[\\/*?:"<>|]', "", title).strip()[:100]  # Limit to 100 chars

def get_video_id(url):
    """Extracts YouTube video ID from different formats"""
    patterns = [
        r"(?:v=|/v/|youtu\.be/|/embed/|/watch\?v=|/shorts/)([A-Za-z0-9_-]{11})"
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None  # Invalid URL

def get_video_title(video_id):
    """Fetch video title using yt-dlp"""
    try:
        with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
            info = ydl.extract_info(f"https://www.youtube.com/watch?v={video_id}", download=False)
            return info.get("title", "Unknown Title")
    except Exception as e:
        return f"Error fetching title: {str(e)}"

@app.route("/get_transcripts", methods=["POST"])
def get_transcripts():
    """API endpoint to fetch transcripts for multiple YouTube videos"""
    data = request.get_json()
    print("Received Data:", data, file=sys.stderr)

    if not data or "urls" not in data:
        return jsonify({"error": "Missing 'urls' parameter"}), 400

    results = []
    processed = {}

    for url in data["urls"]:
        result = {
            "url": url,
            "video_id": None,
            "title": None,
            "transcript": None,
            "error": None
        }

        video_id = get_video_id(url)
        if not video_id:
            result["error"] = "Invalid YouTube URL"
            results.append(result)
            continue

        result["video_id"] = video_id

        if video_id in processed:
            cached = processed[video_id]
            result.update(cached)
            results.append(result)
            continue

        try:
            title = get_video_title(video_id)
            transcript = YouTubeTranscriptApi.get_transcript(video_id)
            transcript_text = " ".join([t["text"] for t in transcript])

            result["title"] = title
            result["transcript"] = transcript_text

            processed[video_id] = {
                "title": title,
                "transcript": transcript_text,
                "error": None
            }

        except Exception as e:
            error_message = f"Error processing video: {str(e)}"
            result["error"] = error_message
            processed[video_id] = {
                "title": None,
                "transcript": None,
                "error": error_message
            }

        results.append(result)

    return jsonify(results)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=True)
