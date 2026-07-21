"""
Distance Tracker:  How Far Are You?

A Python backend for a geolocation based distance widget.

Features:
- Add people by NAME (fully customizable)
- Assign an EMOJI/emotion icon per person (great for family members)
- Calculates real world distance (km/miles) using the Haversine formula (no flat earthers here)
- Designed so it can plug into a Flask API --> feed an iOS widget (via WidgetKit + App Group) or a simple web widget (see the HTML mockup provided alongside this script)

Install:
    pip install geopy break systempackages   #only if you want geopy instead of haversine math

Run:
    python distance_tracker.py
"""

#Import libraries 

import math
import json
import os
from dataclasses import dataclass, field, asdict
from typing import Optional

DATA_FILE = "people.json"


#Core distance math (no external deps needed for now) 
def haversine_distance(lat1, lon1, lat2, lon2, unit="km"):
    """Calculate great circle distance between two (lat, lon) points."""
    R_km = 6371.0
    R_mi = 3958.8
    radius = R_km if unit == "km" else R_mi

    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    d_phi = math.radians(lat2 - lat1)
    d_lambda = math.radians(lon2 - lon1)

    a = (math.sin(d_phi / 2) ** 2
         + math.cos(phi1) * math.cos(phi2) * math.sin(d_lambda / 2) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return round(radius * c, 2)


#  Person model structure database 
@dataclass
class Person:
    name: str
    emoji: str = "🩷"            # default emotion icon for custey effect, this however can be chnage into somehting else
    relationship: str = "Family"  # ex: Mom, Dad, LOML, Sister, Friend
    latitude: Optional[float] = None
    longitude: Optional[float] = None

    def update_location(self, lat, lon):
        self.latitude = lat
        self.longitude = lon


# Manager that stores everyone + computes distances 
class DistanceTracker:
    def __init__(self, my_lat=None, my_lon=None):
        self.my_lat = my_lat
        self.my_lon = my_lon
        self.people = {}  # name/title of Person
        self._load()

    def set_my_location(self, lat, lon):
        self.my_lat = lat
        self.my_lon = lon

    def add_person(self, name, emoji="🩷", relationship="Family", lat=None, lon=None):
        """Add or update a person: fully customizable name + emoji."""
        self.people[name] = Person(name=name, emoji=emoji, relationship=relationship,
                                    latitude=lat, longitude=lon)
        self._save()

    def remove_person(self, name):
        self.people.pop(name, None)
        self._save()

    def update_person_location(self, name, lat, lon):
        if name in self.people:
            self.people[name].update_location(lat, lon)
            self._save()

    def get_distance_to(self, name, unit="km"):
        if self.my_lat is None or self.my_lon is None:
            return None, "Your location isn't set yet."
        person = self.people.get(name)
        if not person or person.latitude is None:
            return None, f"No location on file for {name}."
        dist = haversine_distance(self.my_lat, self.my_lon,
                                   person.latitude, person.longitude, unit)
        return dist, None

    def widget_summary(self, unit="km"):
        """Returns a list of dicts ready to feed a UI/widget."""
        summary = []
        for name, person in self.people.items():
            dist, err = self.get_distance_to(name, unit)
            summary.append({
                "name": name,
                "emoji": person.emoji,
                "relationship": person.relationship,
                "distance": dist,
                "unit": unit,
                "error": err
            })
        return summary

    # simple local persistence 
    def _save(self):
        with open(DATA_FILE, "w") as f:
            json.dump({name: asdict(p) for name, p in self.people.items()}, f, indent=2)

    def _load(self):
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE) as f:
                raw = json.load(f)
            for name, data in raw.items():
                self.people[name] = Person(**data)


#  Example usage 
if __name__ == "__main__":
    tracker = DistanceTracker()

    # Set your own current location (lat, lon) normally pulled from CoreLocation on iOS
    tracker.set_my_location(40.7128, -74.0060)  # ex: New York, NY

    # Add family members — fully customizable name + emoji/emotion
    tracker.add_person("Mom", emoji="🥰", relationship="Mother", lat=34.0522, lon=-118.2437)   # ex: LA
    tracker.add_person("Dad", emoji="🤗", relationship="Father", lat=41.8781, lon=-87.6298)     # ex: Chicago
    tracker.add_person("LOML", emoji="💕", relationship="LOML", lat=51.5074, lon=-0.1278)     # ex: London

    print(json.dumps(tracker.widget_summary(unit="mi"), indent=2))
