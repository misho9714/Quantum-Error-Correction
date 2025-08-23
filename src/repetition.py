import stim
import numpy as np
from IPython.display import SVG

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

# -------- Helpers --------
def bits_to_str(x, one="1", zero="_"):
    return "".join(one if int(b) else zero for b in x)

def decode_min_weight_from_syndrome(s: np.ndarray) -> np.ndarray:
    """
    Input:
      s: shape (d-1,), dtype bool/uint8  [parity of adjacent data qubits]
    Output:
      e_hat: shape (d,), uint8  [min-weight data X pattern consistent with s]
    """
    s = s.astype(np.uint8, copy=False)
    d_minus_1 = s.size
    d = d_minus_1 + 1
    e0 = np.empty(d, dtype=np.uint8)
    e0[0] = 0
    # e0[i] = XOR_{k=0}^{i-1} s[k]
    e0[1:] = np.cumsum(s, dtype=np.uint32) % 2
    w0 = int(e0.sum())
    return e0 if 2 * w0 <= d else 1 - e0

# -------- Circuit (distance = #data qubits, must be odd) --------
def rep_code_with_final_data(distance: int, rounds: int, noise: float) -> stim.Circuit:
    """
    Layout (2*d-1 qubits): d0 a0 d1 a1 ... a_{d-2} d_{d-1}
    Each round:
      - X_ERROR on data (i.i.d. bit-flips)
      - CNOTs from data neighbors into ancilla
      - MR on ancillas (syndrome)
    Finally: M on all data (for majority vote logical)
    """
    if distance % 2 == 0 or distance < 1:
        raise ValueError("Repetition code distance must be odd and >=1.")
    d = distance
    q_total = 2 * d - 1
    data_idx = list(range(0, q_total, 2))            # d data qubits
    anc_idx  = list(range(1, q_total - 1, 2))        # d-1 ancillas

    base = stim.Circuit()
    base.append_operation("X_ERROR", data_idx, noise)
    # Parity check on each ancilla between its two neighbors
    for k, a in enumerate(anc_idx):
        left  = 2 * k      # data k
        right = 2 * (k + 1)  # data k+1
        base.append_operation("CNOT", [left,  a])
        base.append_operation("CNOT", [right, a])
    base.append_operation("MR", anc_idx)

    circuit = base * rounds
    circuit.append_operation("M", data_idx)
    return circuit

# -------- Single-shot run + decoding --------
def distance_d_repetition_code(distance: int, rounds: int, noise: float):
    """
    Returns:
      syndromes: (rounds, d-1)   bool
      frame:     (d,)            uint8  [final Pauli frame estimate]
      data_final:(d,)            uint8
      corrected_data:(d,)        uint8
      raw_logical, corrected_logical, logical_error
    """
    circ = rep_code_with_final_data(distance, rounds, noise)
    rec  = circ.compile_sampler().sample(1)[0]
    d = distance
    s_per_round = d - 1

    syndromes  = rec[: rounds * s_per_round].reshape(rounds, s_per_round)
    data_final = rec[rounds * s_per_round : ].astype(np.uint8)  # length d

    # Time-correlated decoding via running Pauli frame
    frame = np.zeros(d, dtype=np.uint8)
    prev_s = np.zeros(s_per_round, dtype=np.uint8)
    for r in range(rounds):
        # de-noise measurement errors by differencing
        ds   = (syndromes[r].astype(np.uint8) ^ prev_s)
        step = decode_min_weight_from_syndrome(ds).astype(np.uint8)
        frame ^= step
        prev_s = syndromes[r].astype(np.uint8)

    corrected_data = data_final ^ frame

    # Majority vote for |0_L>
    raw_ones = int(data_final.sum())
    cor_ones = int(corrected_data.sum())
    raw_logical = 1 if raw_ones > d // 2 else 0
    cor_logical = 1 if cor_ones > d // 2 else 0
    logical_error = int(cor_logical != 0)

    return {
        "circuit": circ,
        "syndromes": syndromes,            # (rounds, d-1)
        "frame": frame,                    # (d,)
        "data_final": data_final,          # (d,)
        "corrected_data": corrected_data,  # (d,)
        "raw_logical": raw_logical,
        "corrected_logical": cor_logical,
        "logical_error": logical_error,
        "SVG":  SVG(str(circ.diagram("timeline")))
    }

# -------- Fast multi-shot stats --------
def _process_one_record(rec_row: np.ndarray, d: int, rounds: int):
    s_per_round = d - 1
    syndromes  = rec_row[: rounds * s_per_round].reshape(rounds, s_per_round)
    data_final = rec_row[rounds * s_per_round : ].astype(np.uint8)

    frame = np.zeros(d, dtype=np.uint8)
    prev_s = np.zeros(s_per_round, dtype=np.uint8)
    for r in range(rounds):
        ds   = (syndromes[r].astype(np.uint8) ^ prev_s)
        step = decode_min_weight_from_syndrome(ds).astype(np.uint8)
        frame ^= step
        prev_s = syndromes[r].astype(np.uint8)

    corrected_data = data_final ^ frame
    raw_L = 1 if int(data_final.sum())    > d // 2 else 0
    cor_L = 1 if int(corrected_data.sum())> d // 2 else 0
    return dict(raw_logical=raw_L, corrected_logical=cor_L,
                logical_error=int(cor_L != 0))

def collect_stats(distance: int, rounds: int, noise: float, trials: int = 1000, fast: bool = True):
    d = distance
    if d % 2 == 0 or d < 1:
        raise ValueError("Repetition code distance must be odd and >=1.")
    if fast:
        circ = rep_code_with_final_data(d, rounds, noise)
        recs = circ.compile_sampler().sample(trials)
        raw = []
        cor = []
        fails = 0
        example = None
        for i in range(trials):
            res = _process_one_record(recs[i], d, rounds)
            raw.append(res["raw_logical"])
            cor.append(res["corrected_logical"])
            fails += int(res["logical_error"])
            if example is None and res["logical_error"]:
                example = res
    else:
        raw = []
        cor = []
        fails = 0
        example = None
        for _ in range(trials):
            out = distance_d_repetition_code(d, rounds, noise)
            raw.append(out["raw_logical"])
            cor.append(out["corrected_logical"])
            fails += int(out["logical_error"])
            if example is None and out["logical_error"]:
                example = out

    raw_rate = float(np.mean(raw))
    cor_rate = float(np.mean(cor))
    print(f"[distance={d}, rounds={rounds}, noise={noise}, trials={trials}]")
    print(f"Raw logical error rate:       {raw_rate:.6f}")
    print(f"Corrected logical error rate: {cor_rate:.6f}")
    print(f"Failures counted:             {fails}/{trials}")
    return dict(raw_rate=raw_rate, corrected_rate=cor_rate,
                fail_count=fails, trials=trials, example=example)
