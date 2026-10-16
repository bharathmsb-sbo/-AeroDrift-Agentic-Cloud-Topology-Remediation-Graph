import json


class GraphDiff:
    """
    Compares two cloud topology snapshots
    and identifies changes between them.
    """

    def compare(
        self,
        previous_snapshot: dict,
        current_snapshot: dict,
    ) -> dict:
        """
        Compare two saved topology snapshots.
        """

        previous_graph = previous_snapshot["graph_data"]
        current_graph = current_snapshot["graph_data"]

        previous_nodes = {
            node["id"]
            for node in previous_graph["nodes"]
        }

        current_nodes = {
            node["id"]
            for node in current_graph["nodes"]
        }

        previous_edges = {
            self._edge_key(edge)
            for edge in previous_graph["edges"]
        }

        current_edges = {
            self._edge_key(edge)
            for edge in current_graph["edges"]
        }

        added_nodes = current_nodes - previous_nodes
        removed_nodes = previous_nodes - current_nodes

        added_edges = current_edges - previous_edges
        removed_edges = previous_edges - current_edges

        return {
            "added_nodes": sorted(added_nodes),
            "removed_nodes": sorted(removed_nodes),
            "added_edges": sorted(added_edges),
            "removed_edges": sorted(removed_edges),
        }

    def _edge_key(self, edge: dict) -> str:
        """
        Convert an edge into a comparable string.
        """

        return json.dumps(
            {
                "source": edge["source"],
                "target": edge["target"],
                "data": edge["data"],
            },
            sort_keys=True,
        )


def compare_snapshots(
    previous_snapshot: dict,
    current_snapshot: dict,
) -> dict:
    """
    Convenience function for comparing snapshots.
    """

    diff = GraphDiff()

    return diff.compare(
        previous_snapshot,
        current_snapshot,
    )