import argparse
import os
import time
import logging
from dotenv import load_dotenv
from typing import override

import requests

logger = logging.getLogger()
logging.basicConfig(level=logging.INFO)


class Session(requests.Session):
    def __init__(self, api_key: str):
        super().__init__()

        self.base_url: str = "https://api.hedra.com/web-app/public"
        self.headers["x-api-key"] = api_key

    @override
    def prepare_request(self, request: requests.Request) -> requests.PreparedRequest:
        request.url = f"{self.base_url}{request.url}"

        return super().prepare_request(request)


def main():
    # Load environment variables from .env file
    load_dotenv()
    api_key = os.getenv("HEDRA_API_KEY")

    if not api_key:
        # If api_key is still None, it means it wasn't set in the environment
        # AND it wasn't found/loaded from the .env file.
        print("Error: HEDRA_API_KEY not found in environment variables or .env file.")
        return

    # Set up argument parser
    parser = argparse.ArgumentParser(description="Generate video using Hedra API.")
    parser.add_argument(
        '--aspect_ratio',
        type=str,
        required=True,
        choices=['16:9', '9:16', '1:1'],
        help='Aspect ratio for the video (e.g., 16:9, 9:16, 1:1).'
    )
    parser.add_argument(
        '--resolution',
        type=str,
        required=True,
        choices=['540p', '720p'],
        help='Resolution for the video (e.g., 540p, 720p).'
    )
    parser.add_argument(
        '--text_prompt',
        type=str,
        required=True,
        help='Text prompt describing the desired video content.'
    )
    parser.add_argument(
        '--audio_file',
        type=str,
        required=False,
        default=None,
        help='Path to the input audio file. Required unless --voice_id and --voice_text are provided.'
    )
    parser.add_argument(
        '--voice_id',
        type=str,
        required=False,
        default=None,
        help='Voice ID to use for text-to-speech. Use --list_voices to see available voices.'
    )
    parser.add_argument(
        '--voice_text',
        type=str,
        required=False,
        default=None,
        help='Text to convert to speech using the specified voice_id.'
    )
    parser.add_argument(
        '--list_voices',
        action='store_true',
        help='List available voices and exit.'
    )
    parser.add_argument(
        '--image',
        type=str,
        required=True,
        help='Path to the input image file.'
    )
    parser.add_argument(
        '--duration',
        type=float,
        required=False,
        default=None,
        help='Optional duration for the video in seconds (float).'
    )
    parser.add_argument(
        '--seed',
        type=int,
        required=False,
        default=None,
        help='Optional seed for generation (integer).'
    )

    # Parse arguments
    args = parser.parse_args()

    # Initialize Hedra client
    session = Session(api_key=api_key)

    # Handle --list_voices flag
    if args.list_voices:
        voices = session.get("/voices").json()
        print(f"\nAvailable voices ({len(voices)} total):\n")
        print(f"{'ID':<40} {'Name':<20} {'Gender':<10} {'Accent':<15} {'Age':<15}")
        print("-" * 100)
        for voice in voices:
            labels = {l['name']: l['value'] for l in voice.get('asset', {}).get('labels', [])}
            print(f"{voice['id']:<40} {voice['name']:<20} {labels.get('gender', 'N/A'):<10} {labels.get('accent', 'N/A'):<15} {labels.get('age', 'N/A'):<15}")
        return

    # Validate audio input
    if not args.audio_file and not (args.voice_id and args.voice_text):
        print("Error: Either --audio_file or both --voice_id and --voice_text are required.")
        return
    if args.voice_id and not args.voice_text:
        print("Error: --voice_text is required when using --voice_id.")
        return
    if args.voice_text and not args.voice_id:
        print("Error: --voice_id is required when using --voice_text.")
        return

    logger.info("testing against %s", session.base_url)
    model_id = session.get("/models").json()[0]["id"]
    logger.info("got model id %s", model_id)
    model_id = "d1dd37a3-e39a-4854-a298-6510289f9cf2"

    image_response = session.post(
        "/assets",
        json={"name": os.path.basename(args.image), "type": "image"},
    )
    if not image_response.ok:
        logger.error(
            "error creating image: %d %s",
            image_response.status_code,
            image_response.json(),
        )
    image_id = image_response.json()["id"]
    with open(args.image, "rb") as f:
        session.post(f"/assets/{image_id}/upload", files={"file": f}).raise_for_status()
    logger.info("uploaded image %s", image_id)

    # Handle audio: either upload file or use TTS with voice_id
    audio_id = None
    audio_generation = None

    if args.audio_file:
        audio_id = session.post(
            "/assets", json={"name": os.path.basename(args.audio_file), "type": "audio"}
        ).json()["id"]
        with open(args.audio_file, "rb") as f:
            session.post(f"/assets/{audio_id}/upload", files={"file": f}).raise_for_status()
        logger.info("uploaded audio %s", audio_id)
    else:
        # Use TTS with voice_id
        logger.info("using TTS with voice_id %s", args.voice_id)
        audio_generation = {
            "type": "text_to_speech",
            "voice_id": args.voice_id,
            "text": args.voice_text,
        }

    generation_request_data = {
        "type": "video",
        "ai_model_id": model_id,
        "start_keyframe_id": image_id,
        "generated_video_inputs": {
            "text_prompt": args.text_prompt,
            "resolution": args.resolution,
            "aspect_ratio": args.aspect_ratio,
        },
    }

    if audio_id:
        generation_request_data["audio_id"] = audio_id
    if audio_generation:
        generation_request_data["audio_generation"] = audio_generation

    # Add optional parameters if provided
    if args.duration is not None:
        generation_request_data["generated_video_inputs"]["duration_ms"] = int(args.duration * 1000)
    if args.seed is not None:
        generation_request_data["generated_video_inputs"]["seed"] = args.seed

    generation_response = session.post(
        "/generations", json=generation_request_data
    ).json()
    logger.info(generation_response)
    generation_id = generation_response["id"]
    while True:
        status_response = session.get(f"/generations/{generation_id}/status").json()
        logger.info("status response %s", status_response)
        status = status_response["status"]

        # --- Check for completion or error to break the loop ---
        if status in ["complete", "error"]:
            break

        time.sleep(5)

    # --- Process final status (download or log error) ---
    if status == "complete" and status_response.get("url"):
        download_url = status_response["download_url"]
        # Use asset_id for filename if available, otherwise use generation_id
        output_filename_base = status_response.get("asset_id", generation_id)
        output_filename = f"{output_filename_base}.mp4"
        logger.info(f"Generation complete. Downloading video from {download_url} to {output_filename}")
        try:
            # Use a fresh requests get, not the session, as the URL is likely presigned S3
            with requests.get(download_url, stream=True) as r:
                r.raise_for_status() # Check if the request was successful
                with open(output_filename, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        f.write(chunk)
            logger.info(f"Successfully downloaded video to {output_filename}")
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to download video: {e}")
        except IOError as e:
            logger.error(f"Failed to save video file: {e}")
    elif status == "error":
        logger.error(f"Video generation failed: {status_response.get('error_message', 'Unknown error')}")
    else:
        # This case might happen if loop breaks unexpectedly or API changes
        logger.warning(f"Video generation finished with status '{status}' but no download URL was found.")


if __name__ == "__main__":
    main()
