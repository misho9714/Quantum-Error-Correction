import stim

def build_my_surface_code(n: int, rounds: int) -> stim.Circuit:

    L = n*2 - 1
    c = stim.Circuit()
    dat_coords = []
    dat_qubits = []
    for x in range(n):
        for y in range(n):
            dat_coords.append((2 * x, 2 * y))
            dat_qubits.append(2 * x * L + 2 * y)
        if x < n - 1:
            for y in range(n - 1):
                dat_coords.append((2 * x + 1, 2 * y + 1))
                dat_qubits.append((2 * x + 1) * L + 2 * y + 1)

    z_st_coords = []
    z_st_qubits = []
    for x in range(n):
        for y in range(n - 1):
            z_st_coords.append((2 * x, 2 * y + 1))
            z_st_qubits.append(2 * x * L + 2 * y + 1)

    x_st_coords = []
    x_st_qubits = []
    for x in range(n - 1):
        for y in range(n):
            x_st_coords.append((2 * x + 1, 2 * y))
            x_st_qubits.append((2 * x + 1) * L + 2 * y)

    meas_per_round = len(x_st_qubits + z_st_qubits)

    # coords
    for x in range(L):
        for y in range(L):
            c.append("QUBIT_COORDS", [L * x + y], [x, y])

    for t in range(rounds):

        # your Z entangling pattern
        for i in range(len(dat_qubits)):
            if dat_coords[i][0] % 2 == 0 and dat_coords[i][1] < L - 1:
                c.append("CNOT", [dat_qubits[i], dat_qubits[i] + 1])
        c.append("TICK")
        for i in range(len(dat_qubits)):
            if dat_coords[i][0] % 2 == 0 and dat_coords[i][1] > 0:
                c.append("CNOT", [dat_qubits[i], dat_qubits[i] - 1])
        c.append("TICK")
        for i in range(len(dat_qubits)):
            if dat_coords[i][0] % 2 == 1:
                c.append("CNOT", [dat_qubits[i], dat_qubits[i] - L])
        c.append("TICK")
        for i in range(len(dat_qubits)):
            if dat_coords[i][0] % 2 == 1:
                c.append("CNOT", [dat_qubits[i], dat_qubits[i] + L])
        c.append("TICK")

        # measure Z ancillas this round
        c.append("MR", z_st_qubits)
        c.append("TICK")

        # X stabilizers (ancillas in |+>, measure X parity)
        c.append("H", x_st_qubits)
        c.append("TICK")

        # your X entangling pattern
        for i in range(len(dat_qubits)):
            if dat_coords[i][0] % 2 == 0 and dat_coords[i][0] < L - 1:
                c.append("CNOT", [dat_qubits[i] + L, dat_qubits[i]])
        c.append("TICK")
        for i in range(len(dat_qubits)):
            if dat_coords[i][0] % 2 == 0 and dat_coords[i][0] > 0:
                c.append("CNOT", [dat_qubits[i] - L, dat_qubits[i]])
        c.append("TICK")
        for i in range(len(dat_qubits)):
            if dat_coords[i][0] % 2 == 1:
                c.append("CNOT", [dat_qubits[i] - 1, dat_qubits[i]])
        c.append("TICK")
        for i in range(len(dat_qubits)):
            if dat_coords[i][0] % 2 == 1:
                c.append("CNOT", [dat_qubits[i] + 1, dat_qubits[i]])
        c.append("TICK")

        # rotate back to Z basis to use MR
        c.append("H", x_st_qubits)
        c.append("MR", x_st_qubits)
        c.append("TICK")

        # ---- Build detectors as parity between rounds ----
        # NOTE: we rely on measuring [z_st_qubits then x_st_qubits] each round in a fixed order.
        # That makes meas_per_round records per round, in the SAME order every round.
        if t > 0:
            # add detectors for ALL ancilla outcomes this round vs previous round
            for st in range(meas_per_round):
                # current round record index: - (st+1)
                # previous round record index: - (st+1 + meas_per_round)
                c.append(
                    "DETECTOR",
                    [stim.target_rec(-(st+1)), stim.target_rec(-(st+1 + meas_per_round))],
                    [0, st, t]
                )
            c.append("TICK")

    c.append("M", dat_qubits)

    return c