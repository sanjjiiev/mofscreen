# mofscreen

**Automated DFT screening of Metal-Organic Frameworks (MOFs) for Li-ion anode material properties using CP2K.**

Calculates four key properties from a single CIF file:

| # | Property | Method | 
|---|----------|--------|
| 1 | Electronic bandgap | Single-point DFT | 
| 2 | Li adsorption energy | GEO_OPT (MOF + Li) |
| 3 | Formation energy | Instant (reuses #1) | 
| 4 | Volume expansion | Instant (reuses #2) | 

---

## Prerequisites

This library requires **CP2K** to be installed and accessible on your system.

```bash
# Install CP2K via conda (recommended)
conda create -n dft_env python=3.12
conda activate dft_env
conda install -c conda-forge cp2k ase numpy
pip install https://github.com/sanjjiiev/mofscreen/releases/download/v1.0.0/mofscreen-1.0.0-py3-none-any.whl
```

---

## Installation

```bash
# Option 1: Install verified bytecode release directly from GitHub (Python 3.12 required)
pip install https://github.com/sanjjiiev/mofscreen/releases/download/v1.0.0/mofscreen-1.0.0-py3-none-any.whl

# Option 2: Install from PyPI (if Option 1 fails or for future releases)
pip install mofscreen
```

---

## Quick Start — Python API

```python
from mofscreen import MOFScreener

screener = MOFScreener(
    cif_path      = "my_mof.cif",         # your relaxed CIF file
    cores         = 16,                    # CPU cores to use
    cp2k_data_dir = "/home/user/miniconda/envs/dft_env/share/cp2k/data",
)

# ── Run everything (recommended) ──────────────────────────────
results = screener.run_all()

print(f"Bandgap       : {results.bandgap.bandgap_ev:.3f} eV")
print(f"Classification: {results.bandgap.classification}")
print(f"E_ads (Li)    : {results.adsorption.e_ads_ev:.4f} eV")
print(f"E_form/atom   : {results.formation.e_form_per_atom_ev:.4f} eV/atom")
print(f"Volume exp.   : {results.volume.expansion_pct:.2f} %")
```

---

## Run Individual Calculations

You can run any single property without running the full pipeline:

```python
from mofscreen import MOFScreener

screener = MOFScreener(
    cif_path      = "my_mof.cif",
    cores         = 16,
    cp2k_data_dir = "/path/to/cp2k/data",
)

# ── Bandgap only ───────────────────────────────────────────────
bg = screener.calc_bandgap()
print(f"Gap: {bg.bandgap_ev:.3f} eV  [{bg.classification}]")
print(f"HOMO: {bg.homo_ev:.3f} eV | LUMO: {bg.lumo_ev:.3f} eV")

# ── Li adsorption only (inserts 2 Li ions) ─────────────────────
ads = screener.calc_adsorption(n_li=2)
print(f"E_ads: {ads.e_ads_ev:.4f} eV")

# ── Formation energy only ──────────────────────────────────────
fm = screener.calc_formation()
print(f"E_form/atom: {fm.e_form_per_atom_ev:.4f} eV/atom")

# ── Volume expansion only ──────────────────────────────────────
vol = screener.calc_volume()
print(f"Expansion: {vol.expansion_pct:.2f} %")
```

---

## Advanced Options

```python
screener = MOFScreener(
    cif_path      = "my_mof.cif",
    cores         = 32,
    mpi_ranks     = 4,              # hybrid MPI + OpenMP
    cp2k_data_dir = "/path/to/data",
    high_accuracy = True,           # TZV2P basis (publication quality)
    fast_mode     = False,          # set True for quick screening
)

results = screener.run_all(
    n_li         = 4,      # insert 4 Li ions
    cell_opt     = True,   # relax cell vectors (true volume expansion)
    compute_refs = True,   # compute self-consistent elemental references
)
```

---

## Command-Line Interface

After installation, `mofscreen` is available as a CLI command:

```bash
# Full pipeline
mofscreen my_mof.cif --cores 16 --cp2k-data ~/miniconda/envs/dft_env/share/cp2k/data

# Bandgap only
mofscreen my_mof.cif --cores 16 --cp2k-data /path/to/data --only bandgap

# Adsorption with 4 Li ions
mofscreen my_mof.cif --cores 16 --cp2k-data /path/to/data --only adsorption --n-li 4

# High accuracy + compute references
mofscreen my_mof.cif --cores 16 --cp2k-data /path/to/data --high-accuracy --compute-refs

# Set data dir via environment variable instead
export CP2K_DATA_DIR=/home/user/miniconda/envs/dft_env/share/cp2k/data
mofscreen my_mof.cif --cores 16
```

### All CLI options

| Flag | Default | Description |
|------|---------|-------------|
| `--cores` / `-n` | 16 | OMP threads per process |
| `--mpi-ranks` | 1 | MPI ranks (multi-node) |
| `--cp2k-data` | — | Path to CP2K data directory |
| `--only` | — | Run one calc: `bandgap`, `adsorption`, `formation`, `volume` |
| `--n-li` | 1 | Number of Li ions to insert |
| `--cell-opt` | off | Relax cell during adsorption |
| `--high-accuracy` | off | TZV2P basis set |
| `--fast` | off | Lower cutoffs (400 Ry) |
| `--compute-refs` | off | Compute elemental references |
| `--li-ref-ev` | auto | Li reference energy (eV/atom) |
| `--ref-energies` | — | JSON file with reference energies |

---

## Finding Your CP2K Data Directory

```bash
# After conda install cp2k:
conda activate dft_env
python -c "import subprocess, shutil; p=shutil.which('cp2k'); print(p)"

# Typical locations:
# ~/miniconda/envs/dft_env/share/cp2k/data
# ~/anaconda3/envs/dft_env/share/cp2k/data
# /usr/share/cp2k/data

# Verify it contains the right files:
ls ~/miniconda/envs/dft_env/share/cp2k/data/BASIS_MOLOPT
```

---

## Output Files

All outputs are saved in a `results/` folder next to your CIF file:

```
results/
├── bandgap.inp          # CP2K input for bandgap
├── bandgap.out          # CP2K output for bandgap
├── adsorption.inp       # CP2K input for adsorption
├── adsorption.out       # CP2K output for adsorption
├── mof_with_li.cif      # MOF structure with inserted Li
├── elemental_refs/      # Elemental reference calculations
│   └── ref_energies.json
├── summary.json         # All results in JSON format
└── run.log              # Full log of the run
```

---

## Result Fields Reference

### BandgapResult
| Field | Type | Description |
|-------|------|-------------|
| `bandgap_ev` | float | Bandgap in eV (PBE — underestimates by ~30-50%) |
| `classification` | str | `METALLIC`, `SEMI-METAL`, `SEMICONDUCTOR`, `INSULATOR`, etc. |
| `homo_ev` | float | HOMO energy in eV |
| `lumo_ev` | float | LUMO energy in eV |
| `scf_converged` | bool | True if SCF converged |
| `total_energy_ev` | float | Total DFT energy in eV |

### AdsorptionResult
| Field | Type | Description |
|-------|------|-------------|
| `e_ads_ev` | float | Adsorption energy: E(MOF+Li) − E(MOF) − n×E(Li) |
| `relaxed` | bool | True if GEO_OPT converged |
| `n_ions` | int | Number of Li ions inserted |

### FormationResult
| Field | Type | Description |
|-------|------|-------------|
| `e_form_ev` | float | Total formation energy in eV |
| `e_form_per_atom_ev` | float | Formation energy per atom in eV/atom |
| `refs_complete` | bool | True if all elemental references were available |

### VolumeResult
| Field | Type | Description |
|-------|------|-------------|
| `expansion_pct` | float | Volume expansion in % after Li insertion |
| `v_before_A3` | float | Volume of bare MOF in Å³ |
| `v_after_A3` | float | Volume with Li in Å³ |

---

## License

MIT License

---

## Citation

If you use this library in your research, please cite it appropriately.
