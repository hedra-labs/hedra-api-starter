# Hedra API Starter Kit (Python)

This repository provides a Python starter script (`main.py`) for interacting with the Hedra API to generate videos from text prompts, images, and audio.

## Prerequisites

*   **Python 3.8+**
*   **uv**: A fast Python package installer and resolver. If you don't have it, install it following the instructions at [https://github.com/astral-sh/uv](https://github.com/astral-sh/uv).
*   **Hedra API Key**: You need an API key from Hedra, Character-3 is in preview, to get the API key
    * Ensure you're on a paid Hedra plan of at least Creator tier or above.
    * Ensure you've accepted the API ToS at hedra.com/api-profile
    * Email sales@hedra.com with subject line "API Access"

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

**Required Arguments:**

*   `--aspect_ratio`: Aspect ratio for the video. Choices: `16:9`, `9:16`, `1:1`.
*   `--resolution`: Resolution for the video. Choices: `540p`, `720p`.
*   `--text_prompt`: Text prompt describing the desired video content (enclose in quotes if it contains spaces).
*   `--audio_file`: Path to the input audio file (e.g., `.mp3`, `.wav`).
*   `--image`: Path to the input image file (e.g., `.png`, `.jpg`).

**Example:**

```bash
uv run main.py \
    --aspect_ratio 16:9 \
    --resolution 720p \
    --text_prompt "A cute cat astronaut floating in space" \
    --audio_file assets/sample_audio.mp3 \
    --image assets/sample_image.png
```

The script will:
1.  Upload the image and audio assets.
2.  Submit the generation request to the Hedra API.
3.  Poll the API for the status of the generation job.
4.  Once complete, download the generated video file (e.g., `asset_id.mp4`) to the project directory.

Check the console output for progress and the final video file location.
