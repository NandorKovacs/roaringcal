import os
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

# Enable CORS for the frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust this in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Scopes for Google Calendar API
SCOPES = ["https://www.googleapis.com/auth/calendar.readonly"]
CALENDAR_ID = os.getenv("CALENDAR_ID")
SERVICE_ACCOUNT_FILE = os.getenv("GOOGLE_SERVICE_ACCOUNT_FILE")

def get_calendar_service():
    if not SERVICE_ACCOUNT_FILE or not os.path.exists(SERVICE_ACCOUNT_FILE):
        raise HTTPException(
            status_code=500, 
            detail="Service account credentials file not found."
        )
    
    try:
        creds = service_account.Credentials.from_service_account_file(
            SERVICE_ACCOUNT_FILE, scopes=SCOPES
        )
        return build("calendar", "v3", credentials=creds)
    except Exception as e:
        print(f"Error loading credentials: {e}")
        raise HTTPException(status_code=500, detail="Could not initialize Google Calendar service.")

@app.get("/last-updated")
async def get_last_updated():
    try:
        service = get_calendar_service()
        
        # We want the absolute latest modification time. 
        # The 'updated' field on the calendar metadata is often unreliable or reflects 
        # only metadata changes. Instead, we look at the events themselves.
        #
        # orderBy='updated' returns events in ASCENDING order (oldest first).
        # We iterate through all pages to find the very last (most recent) event update.
        
        latest_update = None
        page_token = None
        
        while True:
            # Use singleEvents=False to see the original recurring events' update times
            # and showDeleted=True to include event deletions.
            events_result = service.events().list(
                calendarId=CALENDAR_ID, 
                maxResults=2500, 
                orderBy="updated", 
                showDeleted=True,
                pageToken=page_token,
                singleEvents=False
            ).execute()
            
            items = events_result.get("items", [])
            if items:
                # The last item in the list is the most recently updated in this batch
                latest_update = items[-1].get("updated")
            
            page_token = events_result.get("nextPageToken")
            if not page_token:
                break

        return {"last_updated": latest_update}

    except HttpError as error:
        print(f"An error occurred: {error}")
        raise HTTPException(status_code=500, detail=str(error))
    except Exception as e:
        print(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail="Could not fetch calendar update time.")

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
