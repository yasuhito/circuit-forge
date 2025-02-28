"""Quantum Adder Circuit Generator.

This module generates QASM code for quantum full adder circuits. It implements
n-bit quantum addition using a carry-ripple approach with majority gates.

Usage:
    python -m circuit_forge.adder <number_of_bits>

Where <number_of_bits> must be a multiple of 4.

The generated QASM file will be saved in the 'qasm/' directory with naming
format 'adder_n<total_qubits>.qasm'.

Example:
    python -m circuit_forge.adder 8
    # Generates a quantum circuit for an 8-bit adder and saves it as QASM

"""

import sys
from pathlib import Path

from qiskit import QuantumCircuit
from qiskit.qasm3 import dumps  # type: ignore[import-untyped]


def apply_majority_gate(
    quantum_circuit: QuantumCircuit,
    a: int,
    b: int,
    c: int,
) -> None:
    """Apply majority gate operation for calculating carry bits in quantum addition.

    Args:
        quantum_circuit: Quantum circuit
        a: First qubit index
        b: Second qubit index
        c: Third qubit index (target qubit)

    """
    quantum_circuit.cx(c, b)
    quantum_circuit.cx(c, a)
    quantum_circuit.ccx(a, b, c)


def undo_majority_gate(
    quantum_circuit: QuantumCircuit,
    a: int,
    b: int,
    c: int,
) -> None:
    """Inverse operation of the majority gate.

    Disentangles temporary entanglement.

    Args:
        quantum_circuit: Quantum circuit
        a: First qubit index
        b: Second qubit index
        c: Third qubit index (target qubit)

    """
    quantum_circuit.ccx(a, b, c)
    quantum_circuit.cx(c, a)
    quantum_circuit.cx(a, b)


def add_four_bits(
    quantum_circuit: QuantumCircuit,
    a_qubits: list[int],
    b_qubits: list[int],
    *,
    carry_in: int,
    carry_out: int,
) -> None:
    """Perform 4-bit quantum addition.

    Computes the sum and carry-out from two 4-bit values and a carry-in.

    Args:
        quantum_circuit: Quantum circuit
        a_qubits: First operand qubit indices [a0,a1,a2,a3]
        b_qubits: Second operand qubit indices [b0,b1,b2,b3]
        carry_in: Carry-in qubit index (keyword only)
        carry_out: Carry-out qubit index (keyword only)

    """
    apply_majority_gate(quantum_circuit, carry_in, b_qubits[0], a_qubits[0])
    apply_majority_gate(quantum_circuit, a_qubits[0], b_qubits[1], a_qubits[1])
    apply_majority_gate(quantum_circuit, a_qubits[1], b_qubits[2], a_qubits[2])
    apply_majority_gate(quantum_circuit, a_qubits[2], b_qubits[3], a_qubits[3])
    quantum_circuit.cx(a_qubits[3], carry_out)
    undo_majority_gate(quantum_circuit, a_qubits[2], b_qubits[3], a_qubits[3])
    undo_majority_gate(quantum_circuit, a_qubits[1], b_qubits[2], a_qubits[2])
    undo_majority_gate(quantum_circuit, a_qubits[0], b_qubits[1], a_qubits[1])
    undo_majority_gate(quantum_circuit, carry_in, b_qubits[0], a_qubits[0])


def initialize_quantum_state(
    quantum_circuit: QuantumCircuit,
    qubit_count: int,
    *,
    a_pattern: str,
    b_pattern: str,
    initial_carry: int,
) -> None:
    """Set up the initial state for the quantum adder.

    Args:
        quantum_circuit: Quantum circuit to initialize
        qubit_count: Number of qubits
        a_pattern: Initial bit pattern for first operand (keyword only)
        b_pattern: Initial bit pattern for second operand (keyword only)
        initial_carry: Initial carry value (keyword only)

    """
    a_pattern = a_pattern.ljust(qubit_count, "0")[-qubit_count:]
    b_pattern = b_pattern.ljust(qubit_count, "0")[-qubit_count:]

    for i in range(qubit_count):
        if a_pattern[i] == "1":
            quantum_circuit.x(i)

    for i in range(qubit_count):
        if b_pattern[i] == "1":
            quantum_circuit.x(qubit_count + i)

    if initial_carry == 1:
        quantum_circuit.x(2 * qubit_count)


def validate_qubit_count(qubit_count: int) -> bool:
    """Validate if the number of qubits is valid.

    Args:
        qubit_count: Number of qubits to validate

    Returns:
        bool: True if valid, False otherwise

    """
    return qubit_count % 4 == 0 and qubit_count > 0


def create_quantum_circuit(qubit_count: int) -> tuple[QuantumCircuit, int]:
    """Create a quantum circuit based on the specified number of bits.

    Args:
        qubit_count: Number of bits for the quantum adder

    Returns:
        tuple: (quantum circuit object, total number of qubits)

    """
    n_qubits = qubit_count * 2 + 2 + int(qubit_count / 4) - 1

    return QuantumCircuit(n_qubits, n_qubits), n_qubits


if __name__ == "__main__":
    qubit_count = int(sys.argv[1])

    if not validate_qubit_count(qubit_count):
        sys.exit(0)

    qc, n_qubits = create_quantum_circuit(qubit_count)

    initialize_quantum_state(
        qc,
        qubit_count,
        a_pattern="1110",
        b_pattern="0001",
        initial_carry=1,
    )

    for i in range(0, qubit_count, 4):
        a_qubits = [i, i + 1, i + 2, i + 3]
        b_qubits = [
            i + qubit_count,
            i + qubit_count + 1,
            i + qubit_count + 2,
            i + qubit_count + 3,
        ]
        add_four_bits(
            qc,
            a_qubits,
            b_qubits,
            carry_in=qubit_count * 2 + int(i / 4),
            carry_out=qubit_count * 2 + int(i / 4) + 1,
        )

    qc.measure_all()

    qasm_dir = Path("qasm")
    if not qasm_dir.is_dir():
        qasm_dir.mkdir()

    qasm_path = qasm_dir / f"adder_n{n_qubits}.qasm"
    with qasm_path.open("w") as qasm_file:
        qasm_file.write(dumps(qc))
