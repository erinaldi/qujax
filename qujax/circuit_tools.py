from typing import Sequence, Union, Callable, List, Tuple
import collections.abc

from jax import numpy as jnp


def check_circuit(gate_seq: Sequence[Union[str,
                                           jnp.ndarray,
                                           Callable[[jnp.ndarray], jnp.ndarray],
                                           Callable[[], jnp.ndarray]]],
                  qubit_inds_seq: Sequence[Sequence[int]],
                  param_inds_seq: Sequence[Sequence[int]],
                  n_qubits: int = None):
    """
    Basic checks that circuit arguments conform.

    Args:
        gate_seq: Sequence of gates.
            Each element is either a string matching a function in qujax.gates,
            a unitary array (which will be reshaped into a tensor of shape e.g. (2,2,2,...) )
            or a function taking parameters (can be empty) and returning gate unitary in tensor form.
        qubit_inds_seq: Sequences of qubits (ints) that gates are acting on.
        param_inds_seq: Sequence of parameter indices that gates are using, ie gate 3 uses 1st and 666th parameter.
        n_qubits: Number of qubits, if fixed.

    """
    if not isinstance(gate_seq, collections.abc.Sequence):
        raise TypeError("gate_seq must be Sequence e.g. ['H', 'Rx', 'CX']")

    if (not isinstance(qubit_inds_seq, collections.abc.Sequence)) or \
            (any([not (isinstance(q, collections.abc.Sequence) or hasattr(q, '__array__')) for q in qubit_inds_seq])):
        raise TypeError('qubit_inds_seq must be Sequence of Sequences e.g. [[0,1], [0], []]')

    if (not isinstance(param_inds_seq, collections.abc.Sequence)) or \
            (any([not (isinstance(p, collections.abc.Sequence) or hasattr(p, '__array__')) for p in param_inds_seq])):
        raise TypeError('param_inds_seq must be Sequence of Sequences e.g. [[0,1], [0], []]')

    if len(gate_seq) != len(qubit_inds_seq) or len(param_inds_seq) != len(param_inds_seq):
        raise TypeError(f'gate_seq ({len(gate_seq)}), qubit_inds_seq ({len(qubit_inds_seq)})'
                        f'and param_inds_seq ({len(param_inds_seq)}) must have matching lengths')

    if n_qubits is not None and n_qubits < max([max(qi) for qi in qubit_inds_seq]) + 1:
        raise TypeError('n_qubits must be larger than largest qubit index in qubit_inds_seq')


def _get_gate_str(gate_obj: Union[str,
                                  jnp.ndarray,
                                  Callable[[jnp.ndarray], jnp.ndarray],
                                  Callable[[], jnp.ndarray]],
                  param_inds: Sequence[int]) -> str:
    """
    Maps single gate object to a four character string representation

    Args:
        gate_obj: Either a string matching a function in qujax.gates,
            a unitary array (which will be reshaped into a tensor of shape e.g. (2,2,2,...) )
            or a function taking parameters (can be empty) and returning gate unitary in tensor form.
        param_inds: Parameter indices that gates are using, i.e. gate uses 1st and 666th parameter.

    Returns:
        Four character string representation of the gate

    """
    if isinstance(gate_obj, str):
        gate_str = gate_obj
    else:
        if hasattr(gate_obj, '__name__'):
            gate_str = gate_obj.__name__
        elif hasattr(gate_obj, '__class__') and hasattr(gate_obj.__class__, '__name__'):
            gate_str = gate_obj.__class__.__name__
        else:
            gate_str = 'Other'

    if param_inds == [] or param_inds == [None]:
        if len(gate_str) > 7:
            gate_str = gate_str[:6] + '.'
    else:
        param_str = str(param_inds).replace(' ', '')

        if len(param_str) > 5:
            param_str = '[.]'

        if (len(gate_str) + len(param_str)) > 7:
            gate_str = gate_str[:1] + '.'

        gate_str += param_str

    gate_str = gate_str.center(7, '-')

    return gate_str


def _pad_rows(rows: List[str]) -> Tuple[List[str], List[bool]]:
    """
    Pad string representation of circuit to be rectangular. Fills qubit rows with '-' and between-qubit rows with ' '.

    Args:
        rows: String representation of circuit

    Returns:
        Rectangular string representation of circuit with right padding.

    """

    max_len = max([len(r) for r in rows])

    def extend_row(row: str, qubit_row: bool) -> str:
        lr = len(row)
        if lr < max_len:
            if qubit_row:
                row += '-' * (max_len - lr)
            else:
                row += ' ' * (max_len - lr)
        return row

    out_rows = [extend_row(r, i % 2 == 0) for i, r in enumerate(rows)]
    return out_rows, [True] * len(rows)


def print_circuit(gate_seq: Sequence[Union[str,
                                           jnp.ndarray,
                                           Callable[[jnp.ndarray], jnp.ndarray],
                                           Callable[[], jnp.ndarray]]],
                  qubit_inds_seq: Sequence[Sequence[int]],
                  param_inds_seq: Sequence[Sequence[int]],
                  n_qubits: int = None,
                  qubit_min: int = 0,
                  qubit_max: int = jnp.inf,
                  gate_ind_min: int = 0,
                  gate_ind_max: int = jnp.inf,
                  sep_length: int = 1) -> List[str]:
    """
    Returns and prints basic string representation of circuit.

    Args:
        gate_seq: Sequence of gates.
            Each element is either a string matching a function in qujax.gates,
            a unitary array (which will be reshaped into a tensor of shape e.g. (2,2,2,...) )
            or a function taking parameters (can be empty) and returning gate unitary in tensor form.
        qubit_inds_seq: Sequences of qubits (ints) that gates are acting on.
        param_inds_seq: Sequence of parameter indices that gates are using, ie gate 3 uses 1st and 666th parameter.
        n_qubits: Number of qubits, if fixed.
        qubit_min: Index of first qubit to display
        qubit_max: Index of final qubit to display
        gate_ind_min: Index of gate to start circuit printing
        gate_ind_max: Index of gate to stop circuit printing
        sep_length: Number of dashes to separate gates

    Returns:
        String representation of circuit

    """
    check_circuit(gate_seq, qubit_inds_seq, param_inds_seq, n_qubits)

    gate_ind_max = min(len(gate_seq) - 1, gate_ind_max)
    if gate_ind_max < gate_ind_min:
        raise TypeError('gate_ind_max must be larger or equal to gate_ind_min')

    if n_qubits is None:
        n_qubits = max([max(qi) for qi in qubit_inds_seq]) + 1
    qubit_max = min(n_qubits - 1, qubit_max)

    if qubit_min > qubit_max:
        raise TypeError('qubit_max must be larger or equal to qubit_min')

    gate_str_seq = [_get_gate_str(g, p) for g, p in zip(gate_seq, param_inds_seq)]

    n_qubits_disp = qubit_max - qubit_min + 1

    rows = [f'q{qubit_min}: '.ljust(3) + '-' * sep_length]
    if n_qubits_disp > 1:
        for i in range(qubit_min + 1, qubit_max + 1):
            rows += ['   ', f'q{i}: '.ljust(3) + '-' * sep_length]
    qubits_free = [True] * n_qubits_disp

    for gate_ind in range(gate_ind_min, gate_ind_max + 1):
        g = gate_str_seq[gate_ind]
        qi = qubit_inds_seq[gate_ind]

        qi_min = min(qi)
        qi_max = max(qi)

        if not all([qubits_free[i] for i in range(qi_min, qi_max)]):
            rows, qubits_free = _pad_rows(rows)

        for row_ind in range(2 * qi_min, 2 * qi_max + 1):
            if row_ind == 2 * qi[-1]:
                rows[row_ind] += '-' * sep_length + g
                qubits_free[row_ind // 2] = False
            elif row_ind % 2 == 1:
                rows[row_ind] += ' ' * sep_length + '   ' + '|' + '   '

            elif row_ind / 2 in qi:
                rows[row_ind] += '-' * sep_length + '---' + '◯' + '---'
                qubits_free[row_ind // 2] = False
            else:
                rows[row_ind] += '-' * sep_length + '---' + '|' + '---'
                qubits_free[row_ind // 2] = False

    rows, _ = _pad_rows(rows)

    for p in rows:
        print(p)

    return rows