# RoaringCal

Simple backend to fetch the "last updated" timestamp of a Google Calendar.

## Setup

1.  Ensure you have `uv` installed.
2.  Install dependencies:
    ```bash
    uv sync
    ```
3.  Ensure `client_secret_....json` is in the same directory (already provided).
4.  Run the backend:
    ```bash
    uv run python main.py
    ```

## Authentication

When you run the backend for the first time, a browser window will open for you to authorize the application to read your calendar. Once authorized, a `token.json` file will be created, and you won't need to authorize again.

## Usage

Open `index.html` in your browser. It will automatically query the backend at `http://localhost:8000/last-updated` and display the "Last updated" time in the header.
