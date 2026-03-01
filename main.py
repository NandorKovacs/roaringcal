import os
import os.path
from datetime import datetime
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
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

# If modifying these scopes, delete the file token.json.
SCOPES = ["https://www.googleapis.com/auth/calendar.readonly"]
CALENDAR_ID = os.getenv("CALENDAR_ID")
CLIENT_SECRET_FILE = os.getenv("GOOGLE_CLIENT_SECRET_FILE")
REDIRECT_URI = os.getenv("REDIRECT_URI")

# Store flow state globally for this simple local app
flow_state = {}

def get_calendar_service():
    creds = None
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            raise HTTPException(
                status_code=401, 
                detail="Authentication required. Please visit /auth to start the flow."
            )
        
        with open("token.json", "w") as token:
            token.write(creds.to_json())

    return build("calendar", "v3", credentials=creds)

@app.get("/auth")
async def auth():
    """Returns the authorization URL to the user."""
    flow = InstalledAppFlow.from_client_secrets_file(
        CLIENT_SECRET_FILE, SCOPES, redirect_uri=REDIRECT_URI
    )
    auth_url, _ = flow.authorization_url(prompt='consent')
    
    # Save the code_verifier for the callback
    flow_state["code_verifier"] = flow.code_verifier
    
    return {"auth_url": auth_url}

@app.get("/callback")
async def callback(code: str):
    """Receives the code from the user and saves the token."""
    if "code_verifier" not in flow_state:
        raise HTTPException(status_code=400, detail="No active auth session found. Please go to /auth first.")
        
    flow = InstalledAppFlow.from_client_secrets_file(
        CLIENT_SECRET_FILE, SCOPES, redirect_uri=REDIRECT_URI
    )
    # Re-inject the verifier from the previous step
    flow.code_verifier = flow_state["code_verifier"]
    
    flow.fetch_token(code=code)
    creds = flow.credentials
    with open("token.json", "w") as token:
        token.write(creds.to_json())
    
    # Clean up state
    del flow_state["code_verifier"]
    
    return {"message": "Authentication successful! You can now use the calendar endpoints."}

@app.get("/last-updated")
async def get_last_updated():
    try:
        service = get_calendar_service()
        # Fetch the calendar metadata to get the 'updated' field
        calendar = service.calendars().get(calendarId=CALENDAR_ID).execute()
        updated_time = calendar.get("updated")
        
        if not updated_time:
            # Fallback: check the last modified event if 'updated' is missing
            events_result = service.events().list(
                calendarId=CALENDAR_ID, 
                maxResults=1, 
                orderBy="updated", 
                singleEvents=True
            ).execute()
            events = events_result.get("items", [])
            if events:
                updated_time = events[0].get("updated")

        return {"last_updated": updated_time}

    except HttpError as error:
        print(f"An error occurred: {error}")
        raise HTTPException(status_code=500, detail=str(error))
    except Exception as e:
        print(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail="Could not fetch calendar update time.")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
