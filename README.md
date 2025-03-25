# YouTube API Tutor

1. [Install uv](https://docs.astral.sh/uv/getting-started/installation/#installation-methods) for Python package and environment management.

2. Clone the repository:
    ```bash
    git clone https://github.com/vinhgiga/youtube-api-tutor.git
    ```

3. Navigate to the project directory, you can install all the dependencies using `uv`:
    ```bash
    cd youtube-api-tutor
    uv sync
    ```

4. Then you can activate the virtual environment with:

    ```bash
    source .venv/bin/activate
    ```

    Make sure your editor is using the correct Python virtual environment, with the interpreter at `.venv/bin/python`.

5. Place YOUTUBE_API_KEY in `.env` file. You can get your API key from the [Google Cloud Console](https://console.cloud.google.com/marketplace/product/google/youtube.googleapis.com).

    ```bash
    echo 'YOUTUBE_API_KEY = your_api_key' > .env
    ```

6. Place client_secret.json in the root directory.

7. Run the application:

    ```bash
    uv run main.py
    uv run add_to_playlist.py
    ```
