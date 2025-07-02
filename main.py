from src.hevy.api import HevyAPI
from src.hevy.importer import import_workout_payload

workouts = HevyAPI.get_workouts()
import_workout_payload(workouts)