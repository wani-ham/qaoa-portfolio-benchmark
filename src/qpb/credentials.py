"""Load cloud credentials from .env. The only module that reads secrets."""
import os
from dotenv import load_dotenv

load_dotenv()  # reads .env from the repo root; does nothing if it's missing


def _require(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Missing {name}. Copy .env.example to .env and fill it in.")
    return value


def ibm_service():
    from qiskit_ibm_runtime import QiskitRuntimeService
    return QiskitRuntimeService(
        channel="ibm_quantum_platform",
        token=_require("IBM_QUANTUM_TOKEN"),
        instance=_require("IBM_QUANTUM_INSTANCE"),
    )


def pasqal_connection():
    from pasqal_cloud import PasqalCloudConnection
    return PasqalCloudConnection(
        username=_require("PASQAL_USERNAME"),
        password=_require("PASQAL_PASSWORD"),
        project_id=_require("PASQAL_PROJECT_ID"),
    )