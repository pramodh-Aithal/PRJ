import collections
import csv
import functools

import haversine
import heapq

Airport = collections.namedtuple('Airport', 'code name country latitude longitude')
Flight = collections.namedtuple('Flight', 'origin destination')
Route = collections.namedtuple('Route', 'price path')

class Heap(object):
    """A min-heap."""
    def __init__(self):
        self._values = []
    def push(self, value):
        """Push the value item onto the heap."""
        heapq.heappush(self._values, value)
    def pop(self):
        """ Pop and return the smallest item from the heap."""
        return heapq.heappop(self._values)
    def __len__(self):
        return len(self._values)

def get_airports(path='airports.csv'):
    """Return a generator that yields Airport objects."""
    with open(path, 'rt') as fd:
        reader = csv.reader(fd)
        for row in reader:
            name = row[1]
            country = row[3]
            code = row[4]  # IATA code (eg, 'BCN' for Barcelona)
            latitude = float(row[6])  # Decimal degrees; negative is South.
            longitude = float(row[7])  # Decimal degrees; negative is West.
            yield Airport(code, name, country, latitude, longitude)
# Make it possible to easily look up airports by IATA code.

AIRPORTS = {airport.code: airport for airport in get_airports()}

def get_flights(path='flights.csv'):
    """Return a generator that yields direct Flight objects."""
    with open(path, 'rt') as fd:
        reader = csv.reader(fd)
        for row in reader:
            origin = row[2]  # IATA code of source ...
            destination = row[4]  # ... and destination airport.
            nstops = int(row[7])  # Number of stops; zero for direct.
            if not nstops:
                yield Flight(origin, destination)

class Graph(object):
    """ A hash-table implementation of an undirected graph."""
    def __init__(self):
        # Map each node to a set of nodes connected to it
        self._neighbors = collections.defaultdict(set)
    def connect(self, node1, node2):
        self._neighbors[node1].add(node2)
        self._neighbors[node2].add(node1)
    def neighbors(self, node):
        yield from self._neighbors[node]
    @classmethod
    def load(cls):
        """Return a populated Graph object with real airports and routes."""
        world = cls()
        for flight in get_flights():
            try:
                origin = AIRPORTS[flight.origin]
                destination = AIRPORTS[flight.destination]
                world.connect(origin, destination)
            # Ignore flights to or from an unknown airport
            except KeyError:
                continue
        return world
    @staticmethod
    @functools.lru_cache()
    def get_price(origin, destination, cents_per_km=0.1):
        """Return the cheapest flight without stops."""
        # Haversine distance, in kilometers
        point1 = origin.latitude, origin.longitude,
        point2 = destination.latitude, destination.longitude
        distance = haversine.haversine(point1, point2)
        return distance * cents_per_km
    def dijkstra(self, origin, destination):
        """Use Dijkstra's algorithm to find the cheapest path."""
        routes = Heap()
        for neighbor in self.neighbors(origin):
            price = self.get_price(origin, neighbor)
            routes.push(Route(price=price, path=[origin, neighbor]))
        visited = set()
        visited.add(origin)
        while routes:
            # Find the nearest yet-to-visit airport
            price, path = routes.pop()
            airport = path[-1]
            if airport in visited:
                continue
            # We have arrived! Wo-hoo!
            if airport is destination:
                return price, path
            # Tentative distances to all the unvisited neighbors
            for neighbor in self.neighbors(airport):
                if neighbor not in visited:
                    # Total spent so far plus the price of getting there
                    new_price = price + self.get_price(airport, neighbor)
                    new_path = path + [neighbor]
                    routes.push(Route(new_price, new_path))
            visited.add(airport)
        return float('infinity')

if __name__ == "__main__":
     world = Graph.load()
    valencia = AIRPORTS['VLC']
    portland = AIRPORTS['PDX']
    distance, path = world.dijkstra(valencia, portland)
    print("The shortest path from valencia and portland is")
    print("Airport code",'\t', "Airport name & country")
    for index, airport in enumerate(path):
        print( airport.code,'\t','\t''\t', airport.name,'-',airport.country)
    print("cost = ",distance, '???')
