import math
import pkgutil
from typing import Any, List
from .util.cached_persistent import cached_persistent
import googlemaps
from .secrets import get_secret

cred = get_secret("googlemaps")
gmaps = googlemaps.Client(**get_secret("googlemaps"))

@cached_persistent("geolocate.cache")
def geolocate(*args, **kwargs):
    print(f"Geolocating", *args)
    return gmaps.geocode(*args, **kwargs)

@cached_persistent("distance.cache")
def dist_matrix(srcs: List, dsts: List):
    ret = gmaps.distance_matrix(
        origins=[f"place_id:{location['place_id']}" for location in srcs], 
        destinations=[f"place_id:{location['place_id']}" for location in dsts],
        units="metric"
    )
    return [
        [
            b["distance"]["value"] if b["status"] == "OK" else math.inf
            for b in a["elements"]
        ]
        for a in ret["rows"]
    ]
