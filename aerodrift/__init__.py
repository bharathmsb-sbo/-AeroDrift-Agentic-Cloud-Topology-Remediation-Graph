"""
AeroDrift: Agentic Cloud Topology & Remediation Graph

A self-healing infrastructure engine for enterprise CloudOps that uses graph theory
to detect and automatically remediate configuration drift in cloud environments.
"""

__version__ = "0.1.0"
__author__ = "AeroDrift Team"

from aerodrift.cloud_ingestion import AWSIngestion
from aerodrift.topology_engine import TopologyEngine
from aerodrift.drift_detection import DriftDetector
from aerodrift.code_generator import CodeGenerator
from aerodrift.cli_dashboard import CLIDashboard
from aerodrift.state_persistence import StatePersistence

__all__ = [
    "AWSIngestion",
    "TopologyEngine",
    "DriftDetector",
    "CodeGenerator",
    "CLIDashboard",
    "StatePersistence",
]
