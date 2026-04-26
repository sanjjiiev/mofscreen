"""
Example 5: Adsorption Only (Step 2)
-----------------------------------
Inserts an ion and relaxes the structure. 
REQUIRES: Step 1 (Bandgap) to be completed first to get E(MOF).
"""
import os
from pathlib import Path
from ase.io import read
from mofscreen._core import calc_adsorption_energy, APPROX_ION_REFS, extract_total_energy

cif_file = "test.cif"
out_dir = Path(os.getcwd()) / "results"
bandgap_out = out_dir / "bandgap.out"

# 1. Dependency Check
if not bandgap_out.exists():
    print("ERROR: Missing bandgap.out!")
    print("You must run '04_calc_bandgap_only.py' first to calculate the bare MOF energy.")
    exit(1)

# Extract the real energy from the previous run
actual_e_mof = extract_total_energy(str(bandgap_out))
if actual_e_mof is None:
    print("ERROR: Could not parse total energy from bandgap.out. Did it finish successfully?")
    exit(1)

# 2. Setup and Run
atoms = read(cif_file)
ion_to_test = "K"

print(f"Found E(MOF) = {actual_e_mof:.4f} eV. Starting {ion_to_test} Adsorption...")

ads_result = calc_adsorption_energy(
    atoms=atoms, 
    e_mof=actual_e_mof, 
    out_dir=out_dir, 
    num_cores=16, 
    mpi_ranks=1,
    use_high_accuracy=False, 
    fast_mode=True, 
    n_ions=1, 
    ion_symbol=ion_to_test, 
    cell_opt=True, # Required if you want to run the Volume script next!
    ion_ref_ev=APPROX_ION_REFS[ion_to_test],
    user_mult=None
)

print(f"\n--- Adsorption Results ---")
print(f"Binding Energy: {ads_result.e_ads_ev} eV")