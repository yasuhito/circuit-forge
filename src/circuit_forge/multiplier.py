"""Quantum Multiplier Circuit Generator.

This module generates QASM code for quantum multiplier circuits. It implements
n-bit quantum multiplication using Shift and Add approach with carry operations.

Usage:
    python -m circuit_forge.multiplier <number_of_bits>

Where <number_of_bits> represents the size of the multiplier.

The generated QASM file will be saved in the 'qasm/' directory with naming
format 'multiplier_n<total_qubits>.qasm'.

Example:
    python -m circuit_forge.multiplier 4
    # Generates a quantum circuit for a 4-bit multiplier and saves it as QASM

"""

import math
import random
import sys

from qiskit import ClassicalRegister, QuantumCircuit, QuantumRegister

from circuit_forge.utils import save_qasm_file


def carry(qc: QuantumCircuit, c0: int, a: int, b: int, c1: int) -> None:
    """Apply carry operation for quantum addition.

    Args:
        qc: Quantum circuit
        c0: Previous carry qubit index
        a: First operand qubit index
        b: Second operand qubit index
        c1: Next carry qubit index

    """
    qc.ccx(a, b, c1)
    qc.cx(a, b)
    qc.ccx(c0, b, c1)


def uncarry(qc: QuantumCircuit, c0: int, a: int, b: int, c1: int) -> None:
    """Apply inverse carry operation to disentangle qubits.

    Args:
        qc: Quantum circuit
        c0: Previous carry qubit index
        a: First operand qubit index
        b: Second operand qubit index
        c1: Next carry qubit index

    """
    qc.ccx(c0, b, c1)
    qc.cx(a, b)
    qc.ccx(a, b, c1)


def carry_sum(qc: QuantumCircuit, c0: int, a: int, b: int) -> None:
    """Compute the sum bit in a quantum addition.

    Args:
        qc: Quantum circuit
        c0: Carry qubit index
        a: First operand qubit index
        b: Second operand qubit index (stores the result)

    """
    qc.cx(a, b)
    qc.cx(c0, b)


def adder(qc: QuantumCircuit, qubits: list[int]) -> None:
    """Perform quantum addition on the specified qubits.

    Implements a quantum ripple-carry adder.

    Args:
        qc: Quantum circuit
        qubits: List of qubit indices organized in triplets [c0,a0,b0,c1,a1,b1,...]
                where c are carry qubits, a are first operand qubits,
                and b are second operand qubits

    """
    n = int(len(qubits) / 3)
    c = qubits[0::3]
    a = qubits[1::3]
    b = qubits[2::3]

    for i in range(n - 1):
        carry(qc, c[i], a[i], b[i], c[i + 1])

    carry_sum(qc, c[n - 1], a[n - 1], b[n - 1])

    for i in range(n - 2, -1, -1):
        uncarry(qc, c[i], a[i], b[i], c[i + 1])
        carry_sum(qc, c[i], a[i], b[i])


def multiplier(qc: QuantumCircuit, qubits: list[int]) -> None:
    """Perform quantum multiplication using the shift-and-add method.

    Args:
        qc: Quantum circuit
        qubits: List of all qubits used in the multiplication circuit

    """
    n = int(len(qubits) / 5)
    a = qubits[1 : n * 3 : 3]
    y = qubits[n * 3 : n * 4]
    x = qubits[n * 4 :]

    for i, x_i in enumerate(x):
        for a_qubit, y_qubit in zip(a[i:], y[: n - i], strict=False):
            qc.ccx(x_i, y_qubit, a_qubit)

        adder(qc, qubits[: 3 * n])

        for a_qubit, y_qubit in zip(a[i:], y[: n - i], strict=False):
            qc.ccx(x_i, y_qubit, a_qubit)


def init_bits(qc: QuantumCircuit, x_bin: str, *qubits: int) -> None:
    """Initialize qubits based on a binary string.

    Args:
        qc: Quantum circuit
        x_bin: Binary string representation
        *qubits: Qubit indices to initialize

    """
    for x, qubit in zip(x_bin, list(qubits)[::-1], strict=False):
        if x == "1":
            qc.x(qubit)


def validate_bit_count(n: int) -> bool:
    """Validate if the bit count is appropriate.

    Args:
        n: Number of bits for the multiplier

    Returns:
        bool: True if valid, False otherwise

    """
    return n > 0


def main() -> None:
    """Execute the main multiplier circuit generation program."""
    min_args = 2  # Program name + number of bits

    if len(sys.argv) < min_args:
        sys.stderr.write("Usage: python -m circuit_forge.multiplier <number_of_bits>\n")
        sys.exit(1)

    n = int(sys.argv[1])

    if not validate_bit_count(n):
        sys.stderr.write("Number of bits must be a positive integer.\n")
        sys.exit(1)

    n_qubits = 5 * n
    random.seed(555)  # Fixed seed for reproducibility

    qr = QuantumRegister(n_qubits)
    cr = ClassicalRegister(n)
    qc = QuantumCircuit(qr, cr)

    # Calculate maximum values based on bit width
    maxv = math.floor(math.sqrt(2 ** (n)))
    p = random.randint(1, maxv)  # noqa: S311
    q = random.randint(1, maxv)  # noqa: S311

    y_bin = f"{p:0{n}b}"[-n:]
    x_bin = f"{q:0{n}b}"[-n:]

    # Define qubit groups
    y = qr[n * 3 : n * 4]
    x = qr[n * 4 :]

    # Initialize qubits
    init_bits(qc, x_bin, *x)
    init_bits(qc, y_bin, *y)

    # Apply multiplier circuit
    multiplier(qc, qr)

    # Measure results
    b = qr[2 : n * 3 : 3]  # Result bits for measurement
    qc.measure(b, cr)

    # 共通関数を使用してQASM出力
    save_qasm_file(qc, "multiplier", n_qubits)


if __name__ == "__main__":
    main()
