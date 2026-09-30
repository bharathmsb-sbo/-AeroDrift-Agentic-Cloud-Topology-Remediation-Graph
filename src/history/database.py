import json
import sqlite3
from datetime import datetime
from pathlib import Path

import networkx as nx


class HistoryDatabase:
    """
    Stores historical cloud topology snapshots
    in a SQLite database.
    """

    def __init__(
        self,
        database_path: str = "data/aerodrift_history.db",
    ) -> None:
        """
        Initialize the history database.

        Args:
            database_path: Location of the SQLite database file.
        """

        self.database_path = Path(database_path)

        # Make sure the data directory exists.
        self.database_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

    def initialize(self) -> None:
        """
        Create the snapshots table if it does not exist.
        """

        connection = sqlite3.connect(
            self.database_path
        )

        cursor = connection.cursor()

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS snapshots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT NOT NULL,
                node_count INTEGER NOT NULL,
                edge_count INTEGER NOT NULL,
                graph_data TEXT NOT NULL
            )
            """
        )

        connection.commit()
        connection.close()

    def save_snapshot(
        self,
        graph: nx.DiGraph,
    ) -> None:
        """
        Save the current topology graph as a
        historical snapshot.
        """

        nodes = []

        for node, data in graph.nodes(data=True):
            nodes.append(
                {
                    "id": node,
                    "data": data,
                }
            )

        edges = []

        for source, target, data in graph.edges(data=True):
            edges.append(
                {
                    "source": source,
                    "target": target,
                    "data": data,
                }
            )

        graph_data = {
            "nodes": nodes,
            "edges": edges,
        }

        connection = sqlite3.connect(
            self.database_path
        )

        cursor = connection.cursor()

        cursor.execute(
            """
            INSERT INTO snapshots (
                created_at,
                node_count,
                edge_count,
                graph_data
            )
            VALUES (?, ?, ?, ?)
            """,
            (
                datetime.now().isoformat(),
                graph.number_of_nodes(),
                graph.number_of_edges(),
                json.dumps(graph_data),
            ),
        )

        connection.commit()
        connection.close()

    def get_latest_snapshot(self) -> dict | None:
        """
        Get the most recent topology snapshot
        from the SQLite database.
        """

        connection = sqlite3.connect(
            self.database_path
        )

        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT
                id,
                created_at,
                node_count,
                edge_count,
                graph_data
            FROM snapshots
            ORDER BY id DESC
            LIMIT 1
            """
        )

        row = cursor.fetchone()

        connection.close()

        if row is None:
            return None

        return {
            "id": row[0],
            "created_at": row[1],
            "node_count": row[2],
            "edge_count": row[3],
            "graph_data": json.loads(row[4]),
        }


if __name__ == "__main__":
    from src.topology.graph_engine import build_mock_topology

    graph = build_mock_topology()

    database = HistoryDatabase()

    database.initialize()

    database.save_snapshot(graph)

    print("Snapshot saved successfully.")

    latest_snapshot = database.get_latest_snapshot()

    print("Latest Snapshot:")
    print(latest_snapshot)