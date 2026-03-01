# RoaringCal

Simple backend to fetch the "last updated" timestamp of a Google Calendar.

## Setup

1.  Ensure you have `uv` installed.
2.  Install dependencies:
    ```bash
    uv sync
    ```
3.  Ensure your Google Service Account JSON key file is in the root directory.
4.  Create or update the `.env` file with the following:
    ```
    CALENDAR_ID=your_calendar_id@group.calendar.google.com
    GOOGLE_SERVICE_ACCOUNT_FILE=your-service-account-file.json
    ```
5.  **Important:** Share your Google Calendar with the service account email address (found in the JSON file) with at least "See all event details" permissions.
6.  Run the backend:
    ```bash
    uv run python main.py
    ```

## Usage

Open `index.html` in your browser. It will automatically query the backend at `http://localhost:8000/last-updated` and display the "Last updated" time in the header.
