# Reproducibility record

## Frozen execution host

- Host label: `bear`
- OS/kernel: Ubuntu Linux `6.8.0-134-generic`, x86_64
- Python: 3.12.4
- PyTorch: 2.7.1+cu126; CUDA runtime reported by PyTorch: 12.6
- Transformers: 4.50.0
- scikit-learn: 1.4.2
- NumPy: 1.26.4
- SciPy: 1.13.1
- pytest: 7.4.4
- NVIDIA driver: 560.35.05
- GPUs: A100 80 GB PCIe, H100 PCIe 80 GB, A800 80 GB PCIe

Registry runs used the H100/A100/A800 according to availability; device choice
does not alter the pinned model, deterministic greedy decoder, or stored oracle
table. Greedy decoding used at most 16 new tokens. Every slot permutation and
algorithm seed is derived deterministically from the case ID.

## Frozen model revisions

- `Qwen/Qwen2.5-7B-Instruct`:
  `a09a35458c702b33eeacc393d103063234e8bc28`
- `mistralai/Mistral-7B-Instruct-v0.3`:
  `c170c708c41dac9275d115a8fff4eca08d52bab71`

The server uses locally cached checkpoints recorded by an asset lock.  Absolute
server cache paths are deliberately not required by the code; pass the lock with
`--assets-lock`.

## Verification

Create the declared environment with `conda env create -f environment.yml`, then:

```text
conda run -n coalitiontrace python -m pytest -q
```

The publication snapshot passes 50 tests, including exhaustive verification
of the LOO-backbone ambiguity corollary over every three-variable Boolean
utility satisfying its assumptions. The Windows host's pre-existing
Python 3.9 environment is intentionally unsupported; the project declares Python
3.10 or newer and provides this Python 3.12 environment instead of silently
running under an incompatible interpreter.

Released result hashes are listed in `results/final_manifest.sha256`; the mapping
from manuscript claims to source artifacts is recorded in
`research/CLAIM_RESULT_MANIFEST.md`.
