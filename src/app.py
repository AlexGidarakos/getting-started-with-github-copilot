"""
High School Management System API

A super simple FastAPI application that allows students to view and sign up
for extracurricular activities at Mergington High School.
"""

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
import os
from pathlib import Path
from pymongo import MongoClient
from pymongo.errors import DuplicateKeyError

# MongoDB setup
MONGO_URL = "mongodb://localhost:27017"
DB_NAME = "mergington"
COLLECTION_NAME = "activities"

client = MongoClient(MONGO_URL)
db = client[DB_NAME]
activities_col = db[COLLECTION_NAME]

# Pre-populate activities if collection is empty
hardcoded_activities = {
    "Chess Club": {
        "description": "Learn strategies and compete in chess tournaments",
        "schedule": "Fridays, 3:30 PM - 5:00 PM",
        "max_participants": 12,
        "participants": ["michael@mergington.edu", "daniel@mergington.edu"]
    },
    "Programming Class": {
        "description": "Learn programming fundamentals and build software projects",
        "schedule": "Tuesdays and Thursdays, 3:30 PM - 4:30 PM",
        "max_participants": 20,
        "participants": ["emma@mergington.edu", "sophia@mergington.edu"]
    },
    "Gym Class": {
        "description": "Physical education and sports activities",
        "schedule": "Mondays, Wednesdays, Fridays, 2:00 PM - 3:00 PM",
        "max_participants": 30,
        "participants": ["john@mergington.edu", "olivia@mergington.edu"]
    },
    # Sports activities
    "Soccer Team": {
        "description": "Join the school soccer team and compete in local leagues",
        "schedule": "Tuesdays and Thursdays, 4:00 PM - 5:30 PM",
        "max_participants": 18,
        "participants": ["lucas@mergington.edu", "mia@mergington.edu"]
    },
    "Basketball Club": {
        "description": "Practice basketball skills and play friendly matches",
        "schedule": "Wednesdays, 3:30 PM - 5:00 PM",
        "max_participants": 15,
        "participants": ["liam@mergington.edu", "ava@mergington.edu"]
    },
    # Artistic activities
    "Art Club": {
        "description": "Explore painting, drawing, and other visual arts",
        "schedule": "Mondays, 3:30 PM - 5:00 PM",
        "max_participants": 16,
        "participants": ["noah@mergington.edu", "isabella@mergington.edu"]
    },
    "Drama Society": {
        "description": "Participate in acting, stage production, and school plays",
        "schedule": "Thursdays, 4:00 PM - 5:30 PM",
        "max_participants": 20,
        "participants": ["ethan@mergington.edu", "charlotte@mergington.edu"]
    },
    # Intellectual activities
    "Mathletes": {
        "description": "Compete in math competitions and solve challenging problems",
        "schedule": "Fridays, 2:00 PM - 3:30 PM",
        "max_participants": 10,
        "participants": ["amelia@mergington.edu", "benjamin@mergington.edu"]
    },
    "Science Club": {
        "description": "Conduct experiments and explore scientific concepts",
        "schedule": "Wednesdays, 4:00 PM - 5:00 PM",
        "max_participants": 14,
        "participants": ["elijah@mergington.edu", "harper@mergington.edu"]
    }
}

if activities_col.count_documents({}) == 0:
    for name, details in hardcoded_activities.items():
        doc = {"_id": name, **details}
        try:
            activities_col.insert_one(doc)
        except DuplicateKeyError:
            pass

app = FastAPI(title="Mergington High School API",
              description="API for viewing and signing up for extracurricular activities")

# Mount the static files directory
current_dir = Path(__file__).parent
app.mount("/static", StaticFiles(directory=os.path.join(Path(__file__).parent,
          "static")), name="static")


@app.get("/")
def root():
    return RedirectResponse(url="/static/index.html")


@app.get("/activities")
def get_activities():
    # Fetch all activities from MongoDB and return as dict keyed by activity name
    activities = {}
    for doc in activities_col.find():
        name = doc["_id"]
        details = {k: v for k, v in doc.items() if k != "_id"}
        activities[name] = details
    return activities


@app.post("/activities/{activity_name}/signup")
def signup_for_activity(activity_name: str, email: str):
    """Sign up a student for an activity"""
    doc = activities_col.find_one({"_id": activity_name})
    if not doc:
        raise HTTPException(status_code=404, detail="Activity not found")
    if email in doc["participants"]:
        raise HTTPException(status_code=400, detail="Student already signed up")
    if len(doc["participants"]) >= doc["max_participants"]:
        raise HTTPException(status_code=400, detail="Activity is full")
    activities_col.update_one({"_id": activity_name}, {"$push": {"participants": email}})
    return {"message": f"Signed up {email} for {activity_name}"}


@app.delete("/activities/{activity_name}/unregister")
def unregister_participant(activity_name: str, email: str):
    """Unregister a student from an activity"""
    doc = activities_col.find_one({"_id": activity_name})
    if not doc:
        raise HTTPException(status_code=404, detail="Activity not found")
    if email not in doc["participants"]:
        raise HTTPException(status_code=400, detail="Student not signed up")
    activities_col.update_one({"_id": activity_name}, {"$pull": {"participants": email}})
    return {"message": f"Unregistered {email} from {activity_name}"}
