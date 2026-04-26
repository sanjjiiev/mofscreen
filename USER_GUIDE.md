# mofscreen — User Setup Guide & How to Run

## What is mofscreen?

`mofscreen` is a Python library that automates DFT-based screening of
Metal-Organic Frameworks (MOFs) as alkali/alkaline-earth ion battery anode materials.
It wraps CP2K and computes **7 properties** from a single CIF file:

  1. Electronic bandgap (single-point DFT)
  2. Ion adsorption energy (GEO_OPT of MOF + Ion)
  3. Formation energy (instant, from #1)
  4. Volume expansion (instant, from #2)
  5. **Open-circuit voltage / OCV** (instant, derived from #2)
  6. **Diffusion barrier** (from a pre-computed NEB file)
  7. **Density of states / DOS** (parsed from CP2K PDOS files)

---

## Properties & Formulas

### 1. Electronic Bandgap

Computed from a single-point DFT run using PBE+D3 / DZVP-MOLOPT-SR-GTH.

> ⚠ PBE systematically underestimates the true bandgap by ~30–50%.
> Use `--high-accuracy` (TZV2P) for publication-quality results.

| Classification | Gap range | Meaning for anode |
|---|---|---|
| METALLIC | < 0.01 eV | Good electronic conductivity |
| SEMI-METAL | 0.01–0.5 eV | Acceptable |
| NARROW-GAP SEMICONDUCTOR | 0.5–1.5 eV | Common for conductive MOFs |
| SEMICONDUCTOR | 1.5–3.0 eV | Typical for MOFs |
| WIDE-GAP SEMICONDUCTOR | 3.0–5.0 eV | Needs doping |
| INSULATOR | > 5.0 eV | Poor conductivity |

### 2. Ion Adsorption Energy

Geometry-optimized system (MOF + inserted ions). Formula:

```
E_ads = E(MOF+Ion) − E(MOF) − n × E(Ion_bulk)
```

| E_ads (eV) | Assessment |
|---|---|
| < −1.0 | STRONG — excellent ion storage |
| −1.0 to −0.3 | MODERATE — ion is stable |
| −0.3 to 0 | WEAK — ion barely binds |
| > 0 | UNFAVORABLE — ion won't stay |

### 3. Formation Energy

Derived instantly from the MOF single-point energy (Calc 1). Formula:

```
E_form = E(MOF) − Σ n_i × E(element_i)
```

| E_form/atom | Assessment |
|---|---|
| < −1.0 eV/atom | HIGHLY STABLE |
| < 0 eV/atom | STABLE |
| > 0 eV/atom | UNSTABLE |

### 4. Volume Expansion

Derived from the adsorption calculation (Calc 2). Formula:

```
ΔV% = (V_after − V_before) / V_before × 100
```

| Expansion | Assessment |
|---|---|
| < 1% | EXCELLENT — rigid framework |
| 1–5% | VERY GOOD |
| 5–10% | GOOD — acceptable for anode |
| 10–20% | MODERATE — may limit cycle life |
| > 20% | HIGH — poor cycle stability |

### 5. Open-Circuit Voltage (OCV)

Derived instantly from the adsorption energy — **no extra DFT needed**.

Formula:
```
OCV (V) = −E_ads / (n_ions × z)
```
where `z` is the ion charge (Li/Na/K → 1, Mg/Ca/Zn → 2, Al → 3)
and `E_ads` is in eV, giving the result directly in Volts.

| OCV range | Assessment |
|---|---|
| > 2.0 V | HIGH — may cause electrolyte decomposition |
| 1.0–2.0 V | MODERATE — check electrolyte window |
| 0–1.0 V | LOW — suitable for anode (no dendrite risk) |
| < 0 V | NEGATIVE — thermodynamically unfavorable |

### 6. Diffusion Barrier

Reads a **pre-computed NEB or CI-NEB barrier file** that you supply.
No additional DFT is run by mofscreen itself — run the NEB separately
in CP2K or another code, then point mofscreen to the result.

Accepted file formats:
- **CP2K NEB output** — scanned for `Activation energy: X.XX eV`
- **Plain text file** — first non-comment line contains the barrier in eV

| Barrier | Assessment |
|---|---|
| < 0.3 eV | EXCELLENT — fast ion diffusion |
| 0.3–0.5 eV | GOOD — acceptable kinetics |
| 0.5–0.8 eV | MODERATE — may limit rate capability |
| > 0.8 eV | HIGH — slow ion transport expected |

### 7. Density of States (DOS)

Parses the `.pdos` files that CP2K automatically writes during the bandgap
calculation (produced by the `&PDOS` block in the CP2K input). Enable with `--dos`.

Reports:
- Fermi energy (eV)
- Number of PDOS files found (one per element/spin channel)
- File paths for post-processing with external tools (e.g. sumo, VESTA)

---

## Step 1 — Install CP2K (required dependency)

CP2K is the quantum chemistry engine. Install it once using conda:

```bash
# Create a dedicated DFT environment
conda create -n dft_env python=3.12 -y
conda activate dft_env

# Install CP2K and required packages
conda install -c conda-forge cp2k ase numpy -y
```

Verify CP2K is working:
```bash
cp2k --version
# Should print: CP2K version 2024.x ...
```

---

## Step 2 — Install mofscreen

```bash
conda activate dft_env
pip install mofscreen
```

---

## Step 3 — Find Your CP2K Data Directory

CP2K needs its data files (basis sets, potentials). You must tell
mofscreen where they are. Find your path like this:

```bash
conda activate dft_env

# Find the cp2k binary, then navigate to data:
which cp2k
# e.g. /home/user/miniconda/envs/dft_env/bin/cp2k

# Data is usually at: <conda_env_prefix>/share/cp2k/data
ls ~/miniconda/envs/dft_env/share/cp2k/data/BASIS_MOLOPT
# If this file exists, your data dir is:
# /home/user/miniconda/envs/dft_env/share/cp2k/data
```

Common paths:
  - `~/miniconda/envs/dft_env/share/cp2k/data`
  - `~/anaconda3/envs/dft_env/share/cp2k/data`
  - `~/mambaforge/envs/dft_env/share/cp2k/data`

**Set it permanently in your environment (recommended):**
```bash
echo 'export CP2K_DATA_DIR=~/miniconda/envs/dft_env/share/cp2k/data' >> ~/.bashrc
source ~/.bashrc
```

---

## Step 4 — Prepare Your CIF File

`mofscreen` requires a **relaxed** MOF structure in CIF format.

Requirements for the CIF:
  - Must have periodic boundary conditions (unit cell defined)
  - Should be geometry-optimized (relaxed) before screening
  - File must be readable by ASE (`ase.io.read`)

If your CIF is unrelaxed, the library will warn you:
```
WARNING: Very short bond: 0.75 Å — CIF may be unrelaxed!
```

---

## How to Run — Command Line

### Basic usage (all 7 properties)

```bash
conda activate dft_env
export CP2K_DATA_DIR=~/miniconda/envs/dft_env/share/cp2k/data

# Full pipeline — all properties including OCV (always computed)
mofscreen my_mof.cif --cores 16
```

### With DOS parsing enabled

The DOS is parsed from `.pdos` files written automatically during the
bandgap calculation. Pass `--dos` to activate parsing:

```bash
mofscreen my_mof.cif --cores 16 --dos
```

### With diffusion barrier from a NEB file

Run your CI-NEB calculation separately, then pass the output file:

```bash
# barrier.txt contains just a float, e.g.:   0.42
# or is a CP2K NEB output containing: "Activation energy:  0.42 eV"

mofscreen my_mof.cif --cores 16 --barrier-file barrier.txt
```

### Using a different ion

```bash
# Sodium — 2 ions, with cell relaxation
mofscreen my_mof.cif --cores 16 --ion Na --n-ions 2 --cell-opt

# Potassium — 4 ions
mofscreen my_mof.cif --cores 16 --ion K --n-ions 4

# Magnesium (z=2 — OCV formula uses z=2 automatically)
mofscreen my_mof.cif --cores 16 --ion Mg
```

### With self-consistent elemental references

```bash
mofscreen my_mof.cif --cores 16 --compute-refs
```

### High accuracy (publication quality)

```bash
mofscreen my_mof.cif --cores 32 --mpi-ranks 4 --high-accuracy --compute-refs
```

### Fast screening mode

```bash
mofscreen my_mof.cif --cores 8 --fast
```

### All flags together

```bash
mofscreen my_mof.cif \
    --cores 16 \
    --ion Li \
    --n-ions 1 \
    --dos \
    --barrier-file /path/to/neb_result.txt
```

---

## All CLI Flags Reference

| Flag | Default | Description |
|------|---------|-------------|
| `cif_file` | — | **Required.** Path to your relaxed CIF file |
| `--cores` / `-n` | 16 | OMP threads per process |
| `--mpi-ranks` | 1 | MPI ranks for multi-node runs |
| `--ion` | `Li` | Ion species: `Li`, `Na`, `K`, `Mg`, `Ca`, `Zn`, `Al` |
| `--n-ions` | 1 | Number of ions to insert into the MOF |
| `--cell-opt` | off | Relax cell vectors during adsorption (true volume expansion) |
| `--high-accuracy` | off | Use TZV2P basis set (3–5× slower, publication quality) |
| `--fast` | off | Lower cutoffs (400 Ry) for rapid screening |
| `--compute-refs` | off | Run CP2K to compute self-consistent elemental references |
| `--ion-ref-ev` | auto | Override bulk reference energy for the ion (eV/atom) |
| `--ref-energies` | — | JSON file with pre-computed elemental reference energies |
| `--multiplicity` | auto | Spin multiplicity override |
| `--barrier-file` | — | Path to pre-computed NEB barrier file (eV) |
| `--dos` | off | Parse CP2K PDOS files for density of states |

---

## How to Run — Python API

### Option A: Run Everything (Recommended)

```python
from mofscreen import MOFScreener

screener = MOFScreener(
    cif_path      = "my_mof.cif",
    cores         = 16,                    # adjust to your machine
    cp2k_data_dir = "/home/user/miniconda/envs/dft_env/share/cp2k/data",
)

results = screener.run_all()

# Original 4 properties
print(f"Bandgap       : {results.bandgap.bandgap_ev:.3f} eV")
print(f"Classification: {results.bandgap.classification}")
print(f"E_ads (Li)    : {results.adsorption.e_ads_ev:.4f} eV")
print(f"E_form/atom   : {results.formation.e_form_per_atom_ev:.4f} eV/atom")
print(f"Volume exp.   : {results.volume.expansion_pct:.2f} %")

# 3 additional properties
print(f"OCV           : {results.ocv.ocv_v:.4f} V")
if results.diffusion_barrier.available:
    print(f"Diff. barrier : {results.diffusion_barrier.barrier_ev:.4f} eV")
if results.dos.parsed:
    print(f"Fermi energy  : {results.dos.fermi_ev:.4f} eV  ({results.dos.n_pdos_files} PDOS files)")
```

Save as `run_mof.py` and run:
```bash
conda activate dft_env
python run_mof.py
```

---

### Option B: Run Only Bandgap

```python
from mofscreen import MOFScreener

screener = MOFScreener(
    cif_path      = "my_mof.cif",
    cores         = 16,
    cp2k_data_dir = "/path/to/cp2k/data",
)

result = screener.calc_bandgap()

print(f"Bandgap : {result.bandgap_ev:.3f} eV")
print(f"Type    : {result.classification}")
print(f"HOMO    : {result.homo_ev:.3f} eV")
print(f"LUMO    : {result.lumo_ev:.3f} eV")
print(f"Time    : {result.elapsed_min:.1f} min")
```

---

### Option C: Run Only Ion Adsorption Energy

```python
from mofscreen import MOFScreener

screener = MOFScreener(
    cif_path      = "my_mof.cif",
    cores         = 16,
    cp2k_data_dir = "/path/to/cp2k/data",
)

# Insert 1 Li ion (default)
result = screener.calc_adsorption(ion_symbol="Li", n_ions=1)

# Or test Potassium (K) with 4 ions
result = screener.calc_adsorption(ion_symbol="K", n_ions=4)

print(f"E_ads  : {result.e_ads_ev:.4f} eV")
print(f"Verdict: {'Good anode!' if result.e_ads_ev < -0.3 else 'Weak binding'}")
```

---

### Option D: Run Only Formation Energy

```python
from mofscreen import MOFScreener

screener = MOFScreener(
    cif_path      = "my_mof.cif",
    cores         = 16,
    cp2k_data_dir = "/path/to/cp2k/data",
)

result = screener.calc_formation()

print(f"E_form       : {result.e_form_ev:.4f} eV")
print(f"E_form/atom  : {result.e_form_per_atom_ev:.4f} eV/atom")
print(f"Refs complete: {result.refs_complete}")
```

---

### Option E: Run Only Volume Expansion

```python
from mofscreen import MOFScreener

screener = MOFScreener(
    cif_path      = "my_mof.cif",
    cores         = 16,
    cp2k_data_dir = "/path/to/cp2k/data",
)

result = screener.calc_volume()

print(f"V before : {result.v_before_A3:.2f} Å³")
print(f"V after  : {result.v_after_A3:.2f} Å³")
print(f"Expansion: {result.expansion_pct:.2f} %")
```

---

### Option F: Open-Circuit Voltage

```python
from mofscreen import MOFScreener

screener = MOFScreener(
    cif_path      = "my_mof.cif",
    cores         = 16,
    cp2k_data_dir = "/path/to/cp2k/data",
)

# calc_ocv() automatically runs calc_adsorption() if not already done
result = screener.calc_ocv()

print(f"OCV        : {result.ocv_v:.4f} V")
print(f"Ion charge : {result.z_charge}")
print(f"n_ions     : {result.n_ions}")
```

---

### Option G: Diffusion Barrier

```python
from mofscreen import MOFScreener

screener = MOFScreener(
    cif_path      = "my_mof.cif",
    cores         = 16,
    cp2k_data_dir = "/path/to/cp2k/data",
)

# Pass the path to a pre-computed NEB barrier file
result = screener.calc_diffusion_barrier("neb_result.txt")

if result.available:
    print(f"Barrier    : {result.barrier_ev:.4f} eV")
    print(f"Source     : {result.source_file}")
else:
    print("Barrier file could not be parsed.")
```

---

### Option H: Density of States

```python
from mofscreen import MOFScreener

screener = MOFScreener(
    cif_path      = "my_mof.cif",
    cores         = 16,
    cp2k_data_dir = "/path/to/cp2k/data",
)

# calc_dos() automatically runs calc_bandgap() if not already done
result = screener.calc_dos()

if result.parsed:
    print(f"Fermi energy : {result.fermi_ev:.4f} eV")
    print(f"PDOS files   : {result.n_pdos_files}")
    for f in result.pdos_files:
        print(f"  {f}")
```

---

### Option I: High Accuracy + Self-Consistent References

For publication-quality results:

```python
from mofscreen import MOFScreener

screener = MOFScreener(
    cif_path      = "my_mof.cif",
    cores         = 32,
    mpi_ranks     = 4,                # multi-node MPI
    cp2k_data_dir = "/path/to/cp2k/data",
    high_accuracy = True,             # TZV2P basis set
)

# Compute elemental references first (important for formation energy accuracy)
refs = screener.compute_references(ion_symbol="Na")
print("References computed:", refs)

# Then run full pipeline
results = screener.run_all(
    ion_symbol   = "Na",
    n_ions       = 2,
    cell_opt     = True,    # relax cell (needed for true volume expansion)
    compute_refs = True,
    compute_dos  = True,
)
```

---

## Batch Screening (Multiple MOFs)

To screen many CIF files automatically:

```python
from mofscreen import MOFScreener
import glob
import json
import os

cif_files = glob.glob("mof_dataset/*.cif")
all_results = {}

for cif in cif_files:
    name = os.path.basename(cif).replace(".cif", "")
    print(f"\n{'='*50}")
    print(f"  Screening: {name}")
    print(f"{'='*50}")
    try:
        screener = MOFScreener(
            cif_path      = cif,
            cores         = 16,
            cp2k_data_dir = "/path/to/cp2k/data",
            fast_mode     = True,    # faster for batch screening
        )
        results = screener.run_all()
        all_results[name] = {
            "bandgap_ev"            : results.bandgap.bandgap_ev,
            "classification"        : results.bandgap.classification,
            "e_ads_ev"              : results.adsorption.e_ads_ev,
            "e_form_per_atom_ev"    : results.formation.e_form_per_atom_ev,
            "expansion_pct"         : results.volume.expansion_pct,
            "ocv_v"                 : results.ocv.ocv_v,
            "diffusion_barrier_ev"  : results.diffusion_barrier.barrier_ev,
        }
    except Exception as e:
        print(f"  ERROR for {name}: {e}")
        all_results[name] = {"error": str(e)}

# Save summary
with open("batch_results.json", "w") as f:
    json.dump(all_results, f, indent=2, default=str)

print("\nBatch complete. Results in batch_results.json")
```

---

## Understanding the Output

### Live progress bar during calculation:
```
  ⚙ Bandgap              [████████████░░░░░░░░░░░░░░░░░░░░░░░] 127/300  SCF 127   | E=-45231.2847 eV    2m14s
```

### Result boxes when each calculation finishes:
```
┌──────────────────────────────────────────────────────────────┐
│  ✓  BANDGAP RESULT                                           │
├──────────────────────────────────────────────────────────────┤
│  Gap (PBE)        : 1.8421 eV                                │
│  Classification   : SEMICONDUCTOR                            │
│  HOMO             : -5.2341 eV                               │
│  LUMO             : -3.3920 eV                               │
│  SCF converged    : True                                     │
│  Elapsed          : 24.3 min                                 │
│                                                              │
│  NOTE: PBE underestimates real gap by ~30-50%.               │
└──────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────┐
│  ✓  OPEN-CIRCUIT VOLTAGE RESULT                              │
├──────────────────────────────────────────────────────────────┤
│  OCV              : 0.7843 V  (vs Li+/Li)                    │
│  Ion charge (z)   : 1                                        │
│  n_ions           : 1                                        │
│  Assessment       : LOW — suitable for anode                 │
│                                                              │
│  OCV = -E_ads / (n × z × e)  [eV→V]                         │
└──────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────┐
│  ✓  DIFFUSION BARRIER RESULT                                 │
├──────────────────────────────────────────────────────────────┤
│  Barrier          : 0.4200 eV                                │
│  Source           : /path/to/neb_result.txt                  │
│  Assessment       : GOOD — acceptable kinetics               │
└──────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────┐
│  ✓  DENSITY OF STATES RESULT                                 │
├──────────────────────────────────────────────────────────────┤
│  PDOS files found : 6                                        │
│  Fermi energy     : -5.2341 eV                               │
│  results/mof_bandgap-PDOS-k1-1.pdos                         │
│  results/mof_bandgap-PDOS-k1-2.pdos  ...                    │
└──────────────────────────────────────────────────────────────┘
```

### Final summary (all 7 properties):
```
═════════════════════════════════════════════════════════════════
  FINAL SUMMARY
═════════════════════════════════════════════════════════════════
  MOF: C48H36Fe3N12O12  (111 atoms)  |  Ion: Li×1
  ─────────────────────────────────────────────────────────────
  Bandgap        : 1.8421 eV  [SEMICONDUCTOR]
  E_ads (Li×1)   : -0.7843 eV
  E_form/atom    : -0.4312 eV/atom
  Volume exp.    : 2.143 %
  OCV            : 0.7843 V  (vs Li+/Li)
  Diff. barrier  : 0.4200 eV
  DOS (Fermi)    : -5.2341 eV  [6 PDOS files]
  ─────────────────────────────────────────────────────────────
  Output dir     : /path/to/results/
═════════════════════════════════════════════════════════════════
```

---

## Troubleshooting

**CP2K not found:**
```
ERROR: CP2K not found. Activate your dft_env conda environment.
```
→ Run `conda activate dft_env` before your script.

**CP2K data dir error:**
```
WARNING: CP2K_DATA_DIR not set!
```
→ Pass `cp2k_data_dir=` to `MOFScreener`, or `export CP2K_DATA_DIR=...`

**SCF did not converge:**
```
WARNING: SCF did NOT converge — bandgap unreliable!
```
→ Try increasing `MAX_SCF`, or check if your CIF is properly relaxed.

**No void sites found:**
```
RuntimeError: No void sites found. Ensure CIF is relaxed with open pores.
```
→ Your MOF may not have pores large enough for the ion. The structure should
  be a porous MOF, not a dense solid.

**Very short bond warning:**
```
WARNING: Very short bond: 0.75 Å — CIF may be unrelaxed!
```
→ Your CIF needs geometry optimization before using mofscreen.

**OCV is NOT COMPUTED:**
```
OCV : NOT COMPUTED
```
→ The adsorption energy (E_ads) could not be extracted. Check `adsorption.out`.

**Diffusion barrier NOT PROVIDED:**
```
Diff. barrier : NOT PROVIDED (use --barrier-file)
```
→ This is expected unless you supply a `--barrier-file`. Run CI-NEB
  externally and pass the result file path.

**No PDOS files found:**
```
No .pdos files found in output directory.
```
→ Pass `--dos` and ensure the bandgap calculation ran successfully.
  The `.pdos` files are written by CP2K during the bandgap single-point run.

**Approximate reference energy warning:**
```
⚠ NO Li reference energy found!
   Adsorption energy will be approximate.
```
→ Run with `--compute-refs` or provide `--ion-ref-ev <value>` for an
  accurate ion reference energy.

---

## Output Files Reference

```
results/
├── bandgap.inp              CP2K input for bandgap calculation
├── bandgap.out              CP2K output (contains eigenvalues, etc.)
├── bandgap.out.stderr       Error output from CP2K
├── mof_bandgap-RESTART.wfn  Wavefunction checkpoint (for restarts)
├── *.pdos                   PDOS files per element/spin (DOS source)
├── adsorption.inp           CP2K input for adsorption calc
├── adsorption.out           CP2K output for adsorption
├── mof_with_li.cif          MOF structure with ion(s) inserted
├── elemental_refs/          Elemental reference calculations
│   ├── ref_C.inp / ref_C.out
│   ├── ref_Li.inp / ref_Li.out
│   └── ref_energies.json    Cached reference energies (JSON)
├── summary.json             All 7 results in machine-readable JSON
└── run.log                  Full timestamped log of the run
```

**Restart support:** If a calculation is interrupted (power cut, time limit),
simply re-run the same script. mofscreen automatically detects existing
checkpoint files and resumes from where it left off.

---

## System Requirements

| Requirement | Minimum | Recommended |
|---|---|---|
| CPU cores | 4 | 16–64 |
| RAM | 16 GB | 64+ GB |
| Disk | 5 GB | 50+ GB |
| OS | Linux | Linux |
| Python | 3.9 | 3.11 |
| CP2K | 2023.x | 2024.x |

**Note:** DFT calculations are computationally intensive. A typical MOF
with ~100 atoms takes 30–120 minutes per calculation on 16 cores.

---

*For issues or questions, open an issue on the GitHub repository.*
