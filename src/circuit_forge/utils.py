"""Utility functions for Circuit Forge."""

from pathlib import Path
from typing import Literal

from qiskit import QuantumCircuit
from qiskit.qasm3 import dumps  # type: ignore[import-untyped]


def save_qasm_file(
    qc: QuantumCircuit,
    circuit_type: Literal["adder", "multiplier"],
    n_qubits: int,
) -> Path:
    """Save quantum circuit to QASM file.

    Args:
        qc: Quantum circuit to save
        circuit_type: Type of circuit ("adder" or "multiplier")
        n_qubits: Number of qubits in the circuit

    Returns:
        Path: Path to the saved QASM file

    """
    qasm_dir = Path("qasm")
    if not qasm_dir.is_dir():
        qasm_dir.mkdir()

    qasm_path = qasm_dir / f"{circuit_type}_n{n_qubits}.qasm"
    with qasm_path.open("w") as qasm_file:
        qasm_file.write(dumps(qc))

    return qasm_path
