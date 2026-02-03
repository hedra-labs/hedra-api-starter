# Hedra API Starter Kit (Python)

This repository provides a Python starter script (`main.py`) for interacting with the Hedra API to generate videos from text prompts, images, and audio.

## Prerequisites

*   **Python 3.8+**
*   **uv**: A fast Python package installer and resolver. If you don't have it, install it following the instructions at [https://github.com/astral-sh/uv](https://github.com/astral-sh/uv).
* Ensure you are on paid plan of creator or above at hedra.com/plans
*   **Hedra API Key**: navigate to https://hedra.com/api-profile and accept our terms of service. For volume discounts or use in production reach out to sales@hedra.com


## Setup

1.  **Clone the repository:**
    ```bash
    git clone <repository_url>
    cd hedra-api-starter
    ```

2.  **Set up your API Key:**
    The script requires your Hedra API key. You can provide it in one of two ways:
    *   **Environment Variable:** Set the `HEDRA_API_KEY` environment variable in your shell:
        ```bash
        export HEDRA_API_KEY='your_actual_api_key'
        ```
    *   **.env File:** Create a file named `.env` in the project's root directory and add the following line:
        ```
        HEDRA_API_KEY=your_actual_api_key
        ```
        *(Note: The `.env` file is included in `.gitignore` to prevent accidentally committing your API key.)*

3.  **Install Dependencies:**
    Use `uv` to install the required Python packages listed in `pyproject.toml`:
    ```bash
    uv sync
    ```
    *(This command creates a virtual environment if one doesn't exist and installs/syncs the dependencies.)*

## Usage

Run the `main.py` script using `uv run`, providing the necessary arguments:

```bash
uv run main.py \
    --aspect_ratio <ratio> \
    --resolution <res> \
    --text_prompt "<your_prompt>" \
    --audio_file <path/to/audio.mp3> \
    --image <path/to/image.png>
```

**Command-Line Arguments:**

*   `--aspect_ratio` (Required): Aspect ratio for the video. Choices: `16:9`, `9:16`, `1:1`.
*   `--resolution` (Required): Resolution for the video. Choices: `540p`, `720p`.
*   `--text_prompt` (Required): Text prompt describing the desired video content (enclose in quotes if it contains spaces).
*   `--audio_file` (Conditional): Path to the input audio file (e.g., `.mp3`, `.wav`). Required unless using `--voice_id` and `--voice_text`.
*   `--image` (Required): Path to the input image file (e.g., `.png`, `.jpg`).
*   `--duration` (Optional): Desired duration for the video in seconds (float). Defaults to the length of the audio if not specified.
*   `--seed` (Optional): Seed for the generation process (integer). Allows for reproducible results if the model and other parameters are the same.
*   `--voice_id` (Optional): Voice ID to use for text-to-speech generation. Use with `--voice_text`. Use `--list_voices` to see available voices.
*   `--voice_text` (Optional): Text to convert to speech using the specified `--voice_id`.
*   `--list_voices` (Optional): List all available voices and exit.

**Example (with audio file):**

```bash
uv run main.py \
    --aspect_ratio 9:16 \
    --resolution 540p \
    --text_prompt "A woman talking at the camera" \
    --audio_file assets/audio.wav \
    --image assets/9_16.jpg
```

**Example (with text-to-speech):**

First, list available voices:
```bash
uv run main.py --list_voices
```

Then generate a video using a voice:
```bash
uv run main.py \
    --aspect_ratio 9:16 \
    --resolution 540p \
    --text_prompt "A woman talking at the camera" \
    --voice_id "f412c62f-e94f-41c0-bfc6-97f63289941c" \
    --voice_text "Hello! This is a demonstration of text-to-speech video generation." \
    --image assets/9_16.jpg
```

The script will:
1.  Upload the image and audio assets.
2.  Submit the generation request to the Hedra API.
3.  Poll the API for the status of the generation job.
4.  Once complete, download the generated video file (e.g., `asset_id.mp4`) to the project directory.

Check the console output for progress and the final video file location.
