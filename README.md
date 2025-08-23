# Quantum Error Correction with Stim

This repository explores **quantum error correction (QEC)** using [Stim](https://github.com/quantumlib/Stim).  
We start from the simplest repetition codes and build toward more advanced schemes, analyzing how logical error rates scale with code distance and noise.

---

## Implemented

- **Three-Qubit Repetition Code**  
  Encodes one logical qubit into three physical qubits, corrects a single bit-flip error, and demonstrates syndrome extraction + majority-vote decoding.

- **Distance-d Repetition Codes**  
  Arbitrary odd-distance repetition codes with multiple rounds of syndrome extraction.  
  Includes a **custom Pauli-frame decoder** and direct **comparison of runtime** between:
  - **Stim’s built-in multi-shot sampling** (fast, vectorized), and  
  - **Python loop-based simulation** (clear but slow).  
  We benchmark both speed and logical error rates (raw vs corrected).

---

## Coming Next

- **Surface Code (small patch)** – first step toward 2D topological codes.

---

## Roadmap

- **qLDPC Codes** (modern, scalable approach)  
- **Decoders & Noise Models** – PyMatching, belief propagation, biased/depolarizing noise, correlated noise.

---

## Getting Started

```bash
pip install stim numpy matplotlib pandas
jupyter notebook notebooks/
