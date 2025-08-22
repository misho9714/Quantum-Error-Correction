# Quantum Error Correction with Stim

This repository explores **quantum error correction (QEC)** using [Stim](https://github.com/quantumlib/Stim).  
Starting from the simplest repetition code, we build up to more powerful schemes that protect quantum information from noise.

---

## Implemented

- **Three-Qubit Repetition Code**  
  Encodes one qubit into three, corrects a single bit-flip error, and demonstrates syndrome extraction and majority-vote decoding.

---

## Coming Next

- **Nine-Qubit Shor Code** – corrects both $X$ and $Z$ errors.  
- **General Repetition Codes (n-qubit)** – scaling analysis of logical error rates.

---

## Roadmap

- **7-Qubit Steane Code**  
- **5-Qubit Perfect Code**  
- **Surface Code (small patch)**  
- **qLDPC Codes** (modern, scalable approach)  
- **Decoders & Noise Models** – PyMatching, belief propagation, biased/depolarizing noise.

---

## Example Result

Logical error rate vs. physical error rate for the three-qubit repetition code:

![3-qubit performance plot](plots/three_qubit_logical_vs_physical.png)

---

## Getting Started

```bash
pip install stim numpy matplotlib
jupyter notebook notebooks/
