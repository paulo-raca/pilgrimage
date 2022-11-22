import json
from typing import List
from urllib.parse import quote_plus

from .gmaps import dist_matrix, geolocate

import pygeohash as pgh
import typer
from ortools.constraint_solver import pywrapcp, routing_enums_pb2


app = typer.Typer()


@app.command()
def main(names: List[str] = typer.Argument(...), cyclic: bool = False):
    locations = []
    for name in names:
        geolocate_result = geolocate(name)
        if not geolocate_result:
            raise KeyError(f"Couldn't locate {name}")
        # if len(geolocate_result) > 1:
        #     raise KeyError(
        #         f"Ambiguous resolution of {name}: {' / '.join(l['formatted_address'] for l in geolocate_result)}"
        #     )
        locations.append(geolocate_result[0])

    locations = sorted(
        locations, key=lambda loc: pgh.encode(loc["geometry"]["location"]["lat"], loc["geometry"]["location"]["lng"])
    )
    print("Locations:")
    for i in range(len(locations)):
        print(f' - {locations[i]["formatted_address"]}')

    def distance(a, b):
        if a == len(locations) or b == len(locations):
            return 0

        max = 10
        aa = a // max
        bb = b // max
        distances = dist_matrix(locations[max * aa : max * (aa + 1)], locations[max * bb : max * (bb + 1)])
        ret = distances[a % max][b % max]
        return ret

    manager = pywrapcp.RoutingIndexManager(
        len(locations) if cyclic else len(locations) + 1,  # Num locations
        1,  # Num vehicles
        0 if cyclic else len(locations),  # Starting location
    )

    routing = pywrapcp.RoutingModel(manager)
    routing.SetArcCostEvaluatorOfAllVehicles(
        routing.RegisterTransitCallback(lambda a, b: distance(manager.IndexToNode(a), manager.IndexToNode(b)))
    )

    search_parameters = pywrapcp.DefaultRoutingSearchParameters()
    search_parameters.first_solution_strategy = routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
    solution = routing.SolveWithParameters(search_parameters)

    index = routing.Start(0)
    node = manager.IndexToNode(index)
    route = []
    while True:
        node = manager.IndexToNode(index)
        if node < len(locations):
            route.append(node)
        if routing.IsEnd(index):
            break
        index = solution.Value(routing.NextVar(index))

    route_len = sum([distance(route[i], route[j]) for ni, j in zip(route[:-1], route[1:])])
    print()
    print(f"Solution: {route_len/1000:.1f}km")
    for i in range(len(route)):
        if i > 0:
            print(f"    ... {distance(route[i-1], route[i])/1000:.1f}km ...")
        print(f' {i+1}. {locations[i]["formatted_address"]}')

    url = "https://www.google.com/maps/dir/" + "/".join([quote_plus(locations[i]["formatted_address"]) for i in route])
    print()
    print("Google Maps URL:", url)

    geojson = {
        "type": "LineString",
        "coordinates": [
            [
                locations[i]["geometry"]["location"]["lng"],
                locations[i]["geometry"]["location"]["lat"],
            ]
            for i in route
        ],
    }
    print()
    print("GeoJson:", json.dumps(geojson))

    # TODO: KML
    # kml_namespace = "http://www.opengis.net/kml/2.2"
    # ET.register_namespace("kml", kml_namespace)
    # kml = ET.Element(ET.QName(kml_namespace, "kml"))
    #
    # print(ET.tostring(kml))
