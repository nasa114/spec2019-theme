import os

import requests


def get_location_name(location_id):
    locations = requests.get(os.environ['LOCATION_ENDPOINT']).json()
    return locations[str(location_id)]
