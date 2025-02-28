"""Tests for the quantum adder circuit generator.

This module tests the main functionality of the quantum adder circuit generator,
including:
1. QASM code generation for quantum full adder circuits
2. Core functions of the adder module

"""

from pathlib import Path

import pytest
from qiskit import QuantumCircuit

from circuit_forge.adder import (
    add_four_bits,
    apply_majority_gate,
    create_quantum_circuit,
    initialize_quantum_state,
    main,
    undo_majority_gate,
    validate_qubit_count,
)
from circuit_forge.utils import save_qasm_file


@pytest.fixture(autouse=True)
def cleanup_qasm_files():
    """Fixture to clean up QASM files after tests."""
    qasm_dir = Path("qasm")
    if not qasm_dir.is_dir():
        qasm_dir.mkdir()

    yield

    test_files = [f for f in qasm_dir.iterdir() if f.name.startswith("adder_test_")]
    for file in test_files:
        file.unlink()


def test_validate_qubit_count():
    """Test the validate_qubit_count function."""
    assert validate_qubit_count(4) is True
    assert validate_qubit_count(8) is True
    assert validate_qubit_count(12) is True

    assert validate_qubit_count(0) is False
    assert validate_qubit_count(1) is False
    assert validate_qubit_count(3) is False
    assert validate_qubit_count(-4) is False


def test_create_quantum_circuit():
    """Test the create_quantum_circuit function."""
    qc, n_qubits = create_quantum_circuit(4)
    assert isinstance(qc, QuantumCircuit)
    assert n_qubits == 4 * 2 + 2 + (4 / 4) - 1
    assert qc.num_qubits == 4 * 2 + 2 + (4 / 4) - 1

    qc, n_qubits = create_quantum_circuit(8)
    assert isinstance(qc, QuantumCircuit)
    assert n_qubits == 8 * 2 + 2 + (8 / 4) - 1
    assert qc.num_qubits == 8 * 2 + 2 + (8 / 4) - 1


def test_apply_and_undo_majority_gate():
    """Test the apply_majority_gate and undo_majority_gate functions."""
    qc = QuantumCircuit(3)

    apply_majority_gate(qc, 0, 1, 2)

    apply_depth = qc.depth()
    assert apply_depth > 0

    undo_majority_gate(qc, 0, 1, 2)

    undo_depth = qc.depth()
    assert undo_depth > apply_depth


def test_initialize_quantum_state():
    """Test the initialize_quantum_state function."""
    qc = QuantumCircuit(10)

    initialize_quantum_state(
        qc,
        4,
        a_pattern="1010",
        b_pattern="0101",
        initial_carry=1,
    )

    assert qc.depth() > 0
    assert len(qc.data) > 0


def test_add_four_bits():
    """Test the add_four_bits function."""
    qc = QuantumCircuit(10)

    a_qubits = [0, 1, 2, 3]
    b_qubits = [4, 5, 6, 7]
    carry_in = 8
    carry_out = 9

    add_four_bits(qc, a_qubits, b_qubits, carry_in=carry_in, carry_out=carry_out)

    assert qc.depth() > 0
    assert len(qc.data) > 0


def test_qasm_file_generation():
    """Test generation of QASM file from an adder circuit."""
    qc, n_qubits = create_quantum_circuit(4)

    initialize_quantum_state(qc, 4, a_pattern="1100", b_pattern="0011", initial_carry=0)

    a_qubits = [0, 1, 2, 3]
    b_qubits = [4, 5, 6, 7]
    add_four_bits(
        qc,
        a_qubits,
        b_qubits,
        carry_in=8,
        carry_out=9,
    )

    qasm_path = save_qasm_file(qc, "adder_test", n_qubits)

    assert qasm_path.exists()
    assert qasm_path.stat().st_size > 0

    content = qasm_path.read_text()
    assert "OPENQASM" in content
    assert "qubit" in content


def test_main_integration(monkeypatch: pytest.MonkeyPatch):
    """Test the main function end-to-end."""
    monkeypatch.setattr("sys.argv", ["adder.py", "4"])

    main()

    qasm_path = Path("qasm/adder_n10.qasm")
    assert qasm_path.exists()
    assert qasm_path.stat().st_size > 0
