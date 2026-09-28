class DriftDetector:
    def __init__(self, topology):
        self.topology = topology

    def detect_internet_to_database_path(self):
        graph = {}

        for node in self.topology["nodes"]:
            graph[node["id"]] = []

        for edge in self.topology["edges"]:
            graph[edge["source"]].append(edge["target"])

        internet_nodes = [
            node["id"]
            for node in self.topology["nodes"]
            if node["id"] == "0.0.0.0/0"
        ]

        database_nodes = [
            node["id"]
            for node in self.topology["nodes"]
            if node["type"] == "database"
        ]

        for internet in internet_nodes:
            if self._has_path(internet, database_nodes, graph):
                return True

        return False

    def _has_path(self, start, targets, graph):
        visited = set()
        queue = [start]

        while queue:
            current = queue.pop(0)

            if current in visited:
                continue

            visited.add(current)

            if current in targets:
                return True

            for neighbor in graph.get(current, []):
                if neighbor not in visited:
                    queue.append(neighbor)

        return False