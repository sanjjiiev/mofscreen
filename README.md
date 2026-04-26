# mofscreen

**Automated DFT screening of Metal-Organic Frameworks (MOFs) for multi-ion (Li, Na, K, Mg, Ca, Zn, Al) anode material properties using CP2K.**

Calculates **seven** key properties from a single CIF file:

| # | Property | Method |
|---|----------|--------|
| 1 | Electronic bandgap | Single-point DFT |
| 2 | Ion adsorption energy | GEO_OPT (MOF + Ion) |
| 3 | Formation energy | Instant (reuses #1) |
| 4 | Volume expansion | Instant (reuses #2) |
| 5 | Open-circuit voltage (OCV) | Instant (derived from #2) |
| 6 | Diffusion barrier | From pre-computed NEB file |
| 7 | Density of states (DOS) | Parsed from CP2K PDOS files |

---

## Prerequisites

This library requires **CP2K** to be installed and accessible on your system.

```bash
# Install CP2K via conda (recommended)
conda create -n dft_env python=3.12 -y
conda activate dft_env
conda install -c conda-forge cp2k ase numpy -y
pip install mofscreen
```

---

## Installation

```bash
# Install from PyPI
pip install mofscreen

# Or install the latest wheel directly from GitHub
pip install https://github.com/sanjjiiev/mofscreen/releases/download/v1.1.0/mofscreen-1.1.0-py3-none-any.whl
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
print(f"OCV           : {results.ocv.ocv_v:.4f} V")
if results.diffusion_barrier.available:
    print(f"Diff. barrier : {results.diffusion_barrier.barrier_ev:.4f} eV")
if results.dos.parsed:
    print(f"DOS (Fermi)   : {results.dos.fermi_ev:.4f} eV  [{results.dos.n_pdos_files} PDOS files]")
```

---

## Run Individual Calculations

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

# ── Ion adsorption (inserts 2 Li ions) ──────────────────────────
ads = screener.calc_adsorption(ion_symbol="Li", n_ions=2)
print(f"E_ads: {ads.e_ads_ev:.4f} eV")

# ── Formation energy ───────────────────────────────────────────
fm = screener.calc_formation()
print(f"E_form/atom: {fm.e_form_per_atom_ev:.4f} eV/atom")

# ── Volume expansion ───────────────────────────────────────────
vol = screener.calc_volume()
print(f"Expansion: {vol.expansion_pct:.2f} %")

# ── Open-circuit voltage (derived from adsorption energy) ──────
ocv = screener.calc_ocv()
print(f"OCV: {ocv.ocv_v:.4f} V")

# ── Diffusion barrier (from pre-computed NEB file) ─────────────
db = screener.calc_diffusion_barrier("neb_result.txt")
print(f"Barrier: {db.barrier_ev:.4f} eV")

# ── Density of states (CP2K PDOS files from bandgap calc) ──────
dos = screener.calc_dos()
print(f"Fermi energy: {dos.fermi_ev:.4f} eV  [{dos.n_pdos_files} PDOS files]")
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
    ion_symbol    = "K",            # test Potassium
    n_ions        = 4,              # insert 4 K ions
    cell_opt      = True,           # relax cell vectors (true volume expansion)
    compute_refs  = True,           # compute self-consistent elemental references
    barrier_file  = "neb_k.txt",   # pre-computed NEB barrier
    compute_dos   = True,           # parse CP2K PDOS files
)
```

---

## Command-Line Interface

After installation, `mofscreen` is available as a CLI command:

```bash
# Full pipeline — all 7 properties
mofscreen my_mof.cif --cores 16

# With DOS parsing enabled
mofscreen my_mof.cif --cores 16 --dos

# With diffusion barrier from pre-computed NEB file
mofscreen my_mof.cif --cores 16 --barrier-file neb_result.txt

# Adsorption with 4 K ions
mofscreen my_mof.cif --cores 16 --ion K --n-ions 4

# High accuracy + compute references
mofscreen my_mof.cif --cores 16 --high-accuracy --compute-refs --ion Na

# Fast screening mode
mofscreen my_mof.cif --cores 8 --fast

# Set CP2K data dir via environment variable
export CP2K_DATA_DIR=/home/user/miniconda/envs/dft_env/share/cp2k/data
mofscreen my_mof.cif --cores 16
```

### All CLI options

| Flag | Default | Description |
|------|---------|-------------|
| `--cores` / `-n` | 16 | OMP threads per process |
| `--mpi-ranks` | 1 | MPI ranks (multi-node) |
| `--ion` | `Li` | Ion species: `Li`, `Na`, `K`, `Mg`, `Ca`, `Zn`, `Al` |
| `--n-ions` | 1 | Number of ions to insert |
| `--cell-opt` | off | Relax cell during adsorption |
| `--high-accuracy` | off | TZV2P basis set |
| `--fast` | off | Lower cutoffs (400 Ry) |
| `--compute-refs` | off | Compute elemental references |
| `--ion-ref-ev` | auto | Element reference energy (eV/atom) override |
| `--ref-energies` | — | JSON file with pre-computed energies |
| `--multiplicity` | auto | Spin multiplicity override |
| `--barrier-file` | — | Path to pre-computed NEB barrier file (eV) |
| `--dos` | off | Parse CP2K PDOS files for density of states |

---

## Finding Your CP2K Data Directory

```bash
# After conda install cp2k:
conda activate dft_env
which cp2k
# e.g. /home/user/miniconda/envs/dft_env/bin/cp2k

# Typical data dir locations:
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
├── bandgap.inp              # CP2K input for bandgap
├── bandgap.out              # CP2K output for bandgap
├── bandgap.out.stderr       # stderr from CP2K
├── mof_bandgap-RESTART.wfn  # Wavefunction checkpoint (for restarts)
├── *.pdos                   # PDOS files (one per element/spin — used for DOS)
├── adsorption.inp           # CP2K input for adsorption
├── adsorption.out           # CP2K output for adsorption
├── mof_with_li.cif          # MOF structure with inserted ion
├── elemental_refs/          # Elemental reference calculations
│   ├── ref_Li.inp / ref_Li.out
│   └── ref_energies.json
├── summary.json             # All 7 results in JSON format
└── run.log                  # Full timestamped log of the run
```

**Restart support:** If a calculation is interrupted, simply re-run the same
script. `mofscreen` detects existing checkpoint files and resumes automatically.

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
| `elapsed_min` | float | Wall-clock time in minutes |

### AdsorptionResult
| Field | Type | Description |
|-------|------|-------------|
| `e_ads_ev` | float | Adsorption energy: E(MOF+Ion) − E(MOF) − n×E(Ion) |
| `e_mof_ion_ev` | float | Total energy of MOF+ion system in eV |
| `relaxed` | bool | True if GEO_OPT converged |
| `n_ions` | int | Number of ions inserted |
| `ion_symbol` | str | Ion species (Li, Na, K, …) |
| `elapsed_min` | float | Wall-clock time in minutes |

### FormationResult
| Field | Type | Description |
|-------|------|-------------|
| `e_form_ev` | float | Total formation energy in eV |
| `e_form_per_atom_ev` | float | Formation energy per atom in eV/atom |
| `refs_complete` | bool | True if all elemental references were available |
| `missing_elements` | list[str] | Elements with no reference energy |

### VolumeResult
| Field | Type | Description |
|-------|------|-------------|
| `expansion_pct` | float | Volume expansion in % after insertion |
| `v_before_A3` | float | Volume of bare MOF in Å³ |
| `v_after_A3` | float | Volume with ion in Å³ |
| `cell_relaxed` | bool | True if cell vectors were relaxed |

### OCVResult
| Field | Type | Description |
|-------|------|-------------|
| `ocv_v` | float | Open-circuit voltage in Volts vs Ion⁺/Ion |
| `z_charge` | int | Ion charge (Li/Na/K=1, Mg/Ca/Zn=2, Al=3) |
| `n_ions` | int | Number of ions used |
| `ion_symbol` | str | Ion species |

### DiffusionBarrierResult
| Field | Type | Description |
|-------|------|-------------|
| `barrier_ev` | float | Migration barrier in eV (from NEB) |
| `available` | bool | True if a barrier file was successfully parsed |
| `source_file` | str | Path to the barrier file used |

### DOSResult
| Field | Type | Description |
|-------|------|-------------|
| `fermi_ev` | float | Fermi energy in eV |
| `n_pdos_files` | int | Number of PDOS files found |
| `pdos_files` | list[str] | Paths to all `.pdos` files |
| `parsed` | bool | True if PDOS files were found and parsed |

---

## Bandgap Classification

| Classification | Range | Meaning for Anode |
|---|---|---|
| METALLIC | < 0.01 eV | Good electronic conductivity |
| SEMI-METAL | 0.01–0.5 eV | Acceptable |
| NARROW-GAP SEMICONDUCTOR | 0.5–1.5 eV | Common for conductive MOFs |
| SEMICONDUCTOR | 1.5–3.0 eV | Common for MOFs |
| WIDE-GAP SEMICONDUCTOR | 3.0–5.0 eV | Needs doping |
| INSULATOR | > 5.0 eV | Poor conductivity |

---

## License

MIT License

---

## Citation

If you use this library in your research, please cite it appropriately.
