# from flask import Flask, request, jsonify
# from youtube_transcript_api import YouTubeTranscriptApi
# import re
# import time
# import random

# app = Flask(__name__)

# def get_video_id(url):
#     """Extracts YouTube video ID from different formats"""
#     pattern = r"(?:v=|/v/|youtu\.be/|/embed/|/watch\?v=|/shorts/)([A-Za-z0-9_-]{11})"
#     match = re.search(pattern, url)
#     return match.group(1) if match else None  # Return video ID or None

# def get_transcript(video_id):
#     """Fetches transcript with retries"""
#     for attempt in range(5):  # Retry up to 5 times
#         try:
#             time.sleep(random.uniform(2, 5))  # Random delay to avoid rate limits
#             transcript = YouTubeTranscriptApi.get_transcript(video_id)
#             return " ".join([t["text"] for t in transcript])
#         except Exception as e:
#             if "429" in str(e):  # Too many requests error
#                 wait_time = 2 ** attempt
#                 print(f"Rate limit hit, retrying in {wait_time} seconds...")
#                 time.sleep(wait_time)
#             else:
#                 return None  # Return None on other errors
#     return None  # If all retries fail

# @app.route("/get_transcripts", methods=["POST"])
# def get_transcripts():
#     """API endpoint to fetch transcripts for multiple YouTube videos"""
#     data = request.get_json()
#     if not data or "urls" not in data:
#         return jsonify({"error": "Missing 'urls' parameter"}), 400

#     results = []
#     for url in data["urls"]:
#         video_id = get_video_id(url)
#         transcript = get_transcript(video_id) if video_id else None

#         results.append({
#             "url": url,
#             "video_id": video_id,
#             "transcript": transcript,
#             "error": "Invalid YouTube URL" if not video_id else ("Could not fetch transcript" if not transcript else None)
#         })

#     return jsonify(results)

# if __name__ == "__main__":
#     app.run()


import random
import re
import time

from flask import Flask, jsonify, request
from supabase import Client, create_client
from youtube_transcript_api import YouTubeTranscriptApi

app = Flask(__name__)

# Supabase credentials
SUPABASE_URL = "https://dkemygpazfdnojtkqbmb.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImRrZW15Z3BhemZkbm9qdGtxYm1iIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDIyMzY1ODAsImV4cCI6MjA1NzgxMjU4MH0.AZMr3TVIr3XbneyE4MlLPmaAPS2tqxjX5DVLsGZMLqA"

# Create Supabase client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


def get_video_id(url):
    """Extracts YouTube video ID from different formats"""
    pattern = r"(?:v=|/v/|youtu\.be/|/embed/|/watch\?v=|/shorts/)([A-Za-z0-9_-]{11})"
    match = re.search(pattern, url)
    return match.group(1) if match else None  # Return video ID or None


def get_transcript(video_id):
    """Fetches transcript with retries"""
    for attempt in range(5):  # Retry up to 5 times
        try:
            time.sleep(random.uniform(2, 5))  # Random delay to avoid rate limits
            transcript = YouTubeTranscriptApi.get_transcript(video_id)
            return " ".join([t["text"] for t in transcript])
        except Exception as e:
            if "429" in str(e):  # Too many requests error
                wait_time = 2**attempt
                print(f"Rate limit hit, retrying in {wait_time} seconds...")
                time.sleep(wait_time)
            else:
                return None  # Return None on other errors
    return None  # If all retries fail


def save_to_supabase(video_id, url, transcript):
    """Push transcript data to Supabase"""
    try:
        data = {"video_id": video_id, "url": url, "transcript": transcript}
        response = supabase.table("youtube_transcripts").insert(data).execute()
        print("Supabase response:", response)  # Debug log
        return response
    except Exception as e:
        print(f"Error saving to Supabase: {e}")
        return None


@app.route("/get_transcripts", methods=["POST"])
def get_transcripts():
    """API endpoint to fetch transcripts for multiple YouTube videos"""
    data = request.get_json()
    if not data or "urls" not in data:
        return jsonify({"error": "Missing 'urls' parameter"}), 400

    results = []
    for url in data["urls"]:
        video_id = get_video_id(url)
        transcript = get_transcript(video_id) if video_id else None

        result = {
            "url": url,
            "video_id": video_id,
            "transcript": transcript,
            "error": (
                "Invalid YouTube URL"
                if not video_id
                else ("Could not fetch transcript" if not transcript else None)
            ),
        }

        if video_id and transcript:
            save_to_supabase(video_id, url, transcript)

        results.append(result)

    return jsonify(results)


if __name__ == "__main__":
    app.run()
