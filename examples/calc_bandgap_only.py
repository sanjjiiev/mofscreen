"""
Example 4: Bandgap Only (Step 1)
--------------------------------
Runs the single-point DFT calculation. The Total Energy from this 
run is required before you can run the Adsorption or Formation scripts!
"""
import os
from pathlib import Path
from ase.io import read
from mofscreen._core import calc_bandgap

cif_file = "test.cif"
if not os.path.exists(cif_file):
    print(f"Error: {cif_file} not found.")
    exit(1)

atoms = read(cif_file)
out_dir = Path(os.getcwd()) / "results"
out_dir.mkdir(exist_ok=True)

print("Running Step 1: Bandgap calculation...")

bg_result = calc_bandgap(
    atoms=atoms, 
    out_dir=out_dir, 
    num_cores=16, 
    mpi_ranks=1,
    use_high_accuracy=False, 
    fast_mode=True, 
    user_mult=None
)

print(f"\n--- Bandgap Results ---")
print(f"Bandgap       : {bg_result.bandgap_ev} eV")
print(f"Total E(MOF)  : {bg_result.total_energy_ev} eV")
print("\nSuccess! You can now run the Adsorption or Formation scripts.")