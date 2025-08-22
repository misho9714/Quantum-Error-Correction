import stim
import numpy as np

def three_qubit_code(chance: float, shots: int):
    """Simulate the 3-qubit repetition code under X noise with probability `chance`."""
    circuit = stim.Circuit()
    # --- Encode |0_L>
    circuit.append("CNOT", [0, 1])
    circuit.append("CNOT", [0, 2])

    # --- Apply noise
    circuit.append("X_ERROR", [0, 1, 2], chance)

    # --- Syndrome extraction onto ancillas
    circuit.append("CNOT", [0, 3])
    circuit.append("CNOT", [1, 3])
    circuit.append("CNOT", [1, 4])
    circuit.append("CNOT", [2, 4])

    # --- Measure all qubits
    circuit.append("M", [3, 4, 0, 1, 2])

    # --- Sample ---
    samp = circuit.compile_sampler().sample(shots=shots).astype(np.uint8)
    s01, s12 = samp[:, 0], samp[:, 1]
    d0, d1, d2 = samp[:, 2], samp[:, 3], samp[:, 4]

    # --- Identify corrections ---
    flip0 = (s01 == 1) & (s12 == 0)
    flip1 = (s01 == 1) & (s12 == 1)
    flip2 = (s01 == 0) & (s12 == 1)

    d0c = d0 ^ flip0.astype(np.uint8)
    d1c = d1 ^ flip1.astype(np.uint8)
    d2c = d2 ^ flip2.astype(np.uint8)

    # --- Majority vote decoding ---
    sum_bits = d0c + d1c + d2c
    decoded_logical = (sum_bits >= 2).astype(np.uint8)

    # --- Logical error rate ---
    return decoded_logical.mean()
