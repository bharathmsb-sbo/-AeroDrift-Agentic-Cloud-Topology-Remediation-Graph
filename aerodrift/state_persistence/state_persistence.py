"""
State Persistence: SQLite-based historical state storage and topology diffing.
"""

import sqlite3
import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timezone, timedelta
from pathlib import Path
import threading

logger = logging.getLogger(__name__)


class StatePersistence:
    """
    Manages historical states of the cloud topology in SQLite database.
    
    Features:
    - Save topology snapshots with timestamps
    - Query historical states
    - Generate diffs between two timestamps
    - Maintain audit trail of all changes
    """
    
    def __init__(self, db_path: str = "aerodrift_states.db"):
        """
        Initialize state persistence with SQLite database.
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self.lock = threading.Lock()
        self._initialize_database()
        logger.info(f"State persistence initialized with database: {db_path}")
    
    def _initialize_database(self):
        """Create database schema if it doesn't exist."""
        with self.lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Create topology snapshots table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS topology_snapshots (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    region TEXT NOT NULL,
                    data_json TEXT NOT NULL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create drift events table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS drift_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_id TEXT NOT NULL UNIQUE,
                    timestamp TEXT NOT NULL,
                    drift_type TEXT NOT NULL,
                    severity TEXT NOT NULL,
                    resource_id TEXT NOT NULL,
                    resource_type TEXT NOT NULL,
                    description TEXT NOT NULL,
                    affected_resources TEXT,
                    remediation_required BOOLEAN DEFAULT 1,
                    metadata_json TEXT,
                    remediated BOOLEAN DEFAULT 0,
                    remediation_timestamp TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create remediation actions table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS remediation_actions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_id TEXT NOT NULL,
                    action_type TEXT NOT NULL,
                    resource_id TEXT NOT NULL,
                    parameters_json TEXT NOT NULL,
                    generated_code TEXT NOT NULL,
                    executed BOOLEAN DEFAULT 0,
                    execution_timestamp TEXT,
                    execution_result TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (event_id) REFERENCES drift_events(event_id)
                )
            """)
            
            # Create indexes for better query performance
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_snapshots_timestamp 
                ON topology_snapshots(timestamp)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_drift_events_timestamp 
                ON drift_events(timestamp)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_drift_events_severity 
                ON drift_events(severity)
            """)
            
            conn.commit()
            conn.close()
    
    def save_topology_snapshot(self, topology_data: Dict[str, Any]) -> int:
        """
        Save a topology snapshot to the database.
        
        Args:
            topology_data: Dictionary containing topology state
            
        Returns:
            ID of the inserted snapshot
        """
        with self.lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            timestamp = topology_data.get('timestamp', datetime.now(timezone.utc).isoformat())
            region = topology_data.get('region', 'unknown')
            data_json = json.dumps(topology_data, default=str)
            
            cursor.execute("""
                INSERT INTO topology_snapshots (timestamp, region, data_json)
                VALUES (?, ?, ?)
            """, (timestamp, region, data_json))
            
            snapshot_id = cursor.lastrowid
            conn.commit()
            conn.close()
            
            logger.info(f"Saved topology snapshot {snapshot_id} at {timestamp}")
            return snapshot_id
    
    def get_latest_snapshot(self) -> Optional[Dict[str, Any]]:
        """
        Get the most recent topology snapshot.
        
        Returns:
            Dictionary containing topology data or None if no snapshots exist
        """
        with self.lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT data_json FROM topology_snapshots
                ORDER BY timestamp DESC
                LIMIT 1
            """)
            
            row = cursor.fetchone()
            conn.close()
            
            if row:
                return json.loads(row[0])
            return None
    
    def get_snapshot_by_timestamp(self, timestamp: str) -> Optional[Dict[str, Any]]:
        """
        Get a topology snapshot by timestamp.
        
        Args:
            timestamp: ISO format timestamp string
            
        Returns:
            Dictionary containing topology data or None if not found
        """
        with self.lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT data_json FROM topology_snapshots
                WHERE timestamp = ?
                ORDER BY timestamp DESC
                LIMIT 1
            """, (timestamp,))
            
            row = cursor.fetchone()
            conn.close()
            
            if row:
                return json.loads(row[0])
            return None
    
    def get_snapshot_range(self, start_time: str, end_time: str) -> List[Dict[str, Any]]:
        """
        Get all snapshots within a time range.
        
        Args:
            start_time: ISO format start timestamp
            end_time: ISO format end timestamp
            
        Returns:
            List of topology data dictionaries
        """
        with self.lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT data_json FROM topology_snapshots
                WHERE timestamp BETWEEN ? AND ?
                ORDER BY timestamp ASC
            """, (start_time, end_time))
            
            rows = cursor.fetchall()
            conn.close()
            
            return [json.loads(row[0]) for row in rows]
    
    def save_drift_event(self, drift_event) -> int:
        """
        Save a drift event to the database.
        
        Args:
            drift_event: DriftEvent object
            
        Returns:
            ID of the inserted event
        """
        with self.lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT OR REPLACE INTO drift_events 
                (event_id, timestamp, drift_type, severity, resource_id, 
                 resource_type, description, affected_resources, remediation_required, metadata_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                drift_event.event_id,
                drift_event.timestamp.isoformat(),
                drift_event.drift_type.value,
                drift_event.severity.value,
                drift_event.resource_id,
                drift_event.resource_type,
                drift_event.description,
                json.dumps(drift_event.affected_resources),
                drift_event.remediation_required,
                json.dumps(drift_event.metadata)
            ))
            
            event_id = cursor.lastrowid
            conn.commit()
            conn.close()
            
            logger.info(f"Saved drift event {drift_event.event_id}")
            return event_id
    
    def get_drift_events(self, severity: Optional[str] = None, 
                        limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get drift events from the database.
        
        Args:
            severity: Filter by severity level (optional)
            limit: Maximum number of events to return
            
        Returns:
            List of drift event dictionaries
        """
        with self.lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            if severity:
                cursor.execute("""
                    SELECT * FROM drift_events
                    WHERE severity = ?
                    ORDER BY timestamp DESC
                    LIMIT ?
                """, (severity, limit))
            else:
                cursor.execute("""
                    SELECT * FROM drift_events
                    ORDER BY timestamp DESC
                    LIMIT ?
                """, (limit,))
            
            columns = [desc[0] for desc in cursor.description]
            rows = cursor.fetchall()
            conn.close()
            
            events = []
            for row in rows:
                event_dict = dict(zip(columns, row))
                # Parse JSON fields
                if event_dict.get('affected_resources'):
                    event_dict['affected_resources'] = json.loads(event_dict['affected_resources'])
                if event_dict.get('metadata_json'):
                    event_dict['metadata'] = json.loads(event_dict['metadata_json'])
                events.append(event_dict)
            
            return events
    
    def save_remediation_action(self, event_id: str, action_type: str, 
                               resource_id: str, parameters: Dict[str, Any],
                               generated_code: str) -> int:
        """
        Save a remediation action to the database.
        
        Args:
            event_id: Associated drift event ID
            action_type: Type of remediation action
            resource_id: Target resource ID
            parameters: Action parameters
            generated_code: Generated Python code
            
        Returns:
            ID of the inserted action
        """
        with self.lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO remediation_actions
                (event_id, action_type, resource_id, parameters_json, generated_code)
                VALUES (?, ?, ?, ?, ?)
            """, (
                event_id,
                action_type,
                resource_id,
                json.dumps(parameters),
                generated_code
            ))
            
            action_id = cursor.lastrowid
            conn.commit()
            conn.close()
            
            logger.info(f"Saved remediation action {action_id} for event {event_id}")
            return action_id
    
    def mark_event_remediated(self, event_id: str, success: bool = True):
        """
        Mark a drift event as remediated.
        
        Args:
            event_id: Drift event ID
            success: Whether remediation was successful
        """
        with self.lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                UPDATE drift_events
                SET remediated = 1, remediation_timestamp = ?
                WHERE event_id = ?
            """, (datetime.now(timezone.utc).isoformat(), event_id))
            
            conn.commit()
            conn.close()
            
            logger.info(f"Marked event {event_id} as remediated (success={success})")
    
    def generate_topology_diff(self, timestamp1: str, timestamp2: str) -> Dict[str, Any]:
        """
        Generate a diff between two topology snapshots.
        
        Args:
            timestamp1: First timestamp (baseline)
            timestamp2: Second timestamp (current)
            
        Returns:
            Dictionary containing the diff
        """
        snapshot1 = self.get_snapshot_by_timestamp(timestamp1)
        snapshot2 = self.get_snapshot_by_timestamp(timestamp2)
        
        if not snapshot1 or not snapshot2:
            logger.error("One or both snapshots not found for diff")
            return {}
        
        diff = {
            'timestamp1': timestamp1,
            'timestamp2': timestamp2,
            'vpcs': self._diff_resources(snapshot1.get('vpcs', []), snapshot2.get('vpcs', [])),
            'subnets': self._diff_resources(snapshot1.get('subnets', []), snapshot2.get('subnets', [])),
            'security_groups': self._diff_resources(snapshot1.get('security_groups', []), 
                                                   snapshot2.get('security_groups', [])),
            'instances': self._diff_resources(snapshot1.get('instances', []), snapshot2.get('instances', []))
        }
        
        logger.info(f"Generated topology diff between {timestamp1} and {timestamp2}")
        return diff
    
    def _diff_resources(self, resources1: List[Any], resources2: List[Any]) -> Dict[str, List[Any]]:
        """
        Diff two lists of resources.
        
        Args:
            resources1: First list of resources
            resources2: Second list of resources
            
        Returns:
            Dictionary with 'added', 'removed', and 'modified' resources
        """
        # Convert to dictionaries by ID for easier comparison
        dict1 = {getattr(r, 'vpc_id' if hasattr(r, 'vpc_id') else 
                        'subnet_id' if hasattr(r, 'subnet_id') else
                        'group_id' if hasattr(r, 'group_id') else
                        'instance_id', ''): r for r in resources1}
        dict2 = {getattr(r, 'vpc_id' if hasattr(r, 'vpc_id') else 
                        'subnet_id' if hasattr(r, 'subnet_id') else
                        'group_id' if hasattr(r, 'group_id') else
                        'instance_id', ''): r for r in resources2}
        
        ids1 = set(dict1.keys())
        ids2 = set(dict2.keys())
        
        added_ids = ids2 - ids1
        removed_ids = ids1 - ids2
        common_ids = ids1 & ids2
        
        added = [dict2[id] for id in added_ids]
        removed = [dict1[id] for id in removed_ids]
        
        # For common resources, check if they're modified
        modified = []
        for id in common_ids:
            # Simple comparison - in production, you'd do field-by-field comparison
            if dict1[id] != dict2[id]:
                modified.append({
                    'resource_id': id,
                    'old': dict1[id],
                    'new': dict2[id]
                })
        
        return {
            'added': added,
            'removed': removed,
            'modified': modified
        }
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get database statistics.
        
        Returns:
            Dictionary containing statistics
        """
        with self.lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Count snapshots
            cursor.execute("SELECT COUNT(*) FROM topology_snapshots")
            snapshot_count = cursor.fetchone()[0]
            
            # Count drift events
            cursor.execute("SELECT COUNT(*) FROM drift_events")
            event_count = cursor.fetchone()[0]
            
            # Count remediated events
            cursor.execute("SELECT COUNT(*) FROM drift_events WHERE remediated = 1")
            remediated_count = cursor.fetchone()[0]
            
            # Count by severity
            cursor.execute("""
                SELECT severity, COUNT(*) 
                FROM drift_events 
                GROUP BY severity
            """)
            severity_counts = dict(cursor.fetchall())
            
            conn.close()
        
        return {
            'total_snapshots': snapshot_count,
            'total_drift_events': event_count,
            'remediated_events': remediated_count,
            'pending_remediation': event_count - remediated_count,
            'severity_breakdown': severity_counts
        }
    
    def cleanup_old_snapshots(self, days_to_keep: int = 30):
        """
        Remove snapshots older than specified days.
        
        Args:
            days_to_keep: Number of days to keep snapshots
        """
        with self.lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            from datetime import timedelta
            cutoff_date = (datetime.utcnow() - 
                          timedelta(days=days_to_keep)).isoformat()
            
            cursor.execute("""
                DELETE FROM topology_snapshots
                WHERE timestamp < ?
            """, (cutoff_date,))
            
            deleted_count = cursor.rowcount
            conn.commit()
            conn.close()
            
            logger.info(f"Cleaned up {deleted_count} old snapshots")
    
    def export_data(self, output_path: str = "aerodrift_export.json"):
        """
        Export all data to a JSON file.
        
        Args:
            output_path: Path to output JSON file
        """
        with self.lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Export snapshots
            cursor.execute("SELECT data_json FROM topology_snapshots")
            snapshots = [json.loads(row[0]) for row in cursor.fetchall()]
            
            # Export drift events
            cursor.execute("SELECT * FROM drift_events")
            columns = [desc[0] for desc in cursor.description]
            events = []
            for row in cursor.fetchall():
                event_dict = dict(zip(columns, row))
                if event_dict.get('affected_resources'):
                    event_dict['affected_resources'] = json.loads(event_dict['affected_resources'])
                if event_dict.get('metadata_json'):
                    event_dict['metadata'] = json.loads(event_dict['metadata_json'])
                events.append(event_dict)
            
            conn.close()
        
        export_data = {
            'export_timestamp': datetime.utcnow().isoformat(),
            'snapshots': snapshots,
            'drift_events': events
        }
        
        with open(output_path, 'w') as f:
            json.dump(export_data, f, indent=2, default=str)
        
        logger.info(f"Exported data to {output_path}")
