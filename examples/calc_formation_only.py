"""
Example 6: Formation Energy Only (Step 3)
-----------------------------------------
Calculates thermodynamic stability.
REQUIRES: Step 1 (Bandgap) to be completed first.
"""
import os
from pathlib import Path
from ase.io import read
from mofscreen._core import calc_formation_energy, extract_total_energy, load_reference_energies

cif_file = "test.cif"
out_dir = Path(os.getcwd()) / "results"
bandgap_out = out_dir / "bandgap.out"
ref_file = out_dir / "elemental_refs" / "ref_energies.json"

# 1. Check for Step 1 Energy
if not bandgap_out.exists() or extract_total_energy(str(bandgap_out)) is None:
    print("ERROR: Missing or incomplete bandgap.out!")
    print("You must run '04_calc_bandgap_only.py' first.")
    exit(1)

actual_e_mof = extract_total_energy(str(bandgap_out))

# 2. Check for References
refs = load_reference_energies(ref_file)
if not refs:
    print("WARNING: 'ref_energies.json' not found.")
    print("To get exact formation energies, run the main CLI tool with the '--compute-refs' flag.")
    print("Will attempt calculation anyway (may result in missing references)...\n")

# 3. Run Math
atoms = read(cif_file)
print("Calculating Formation Energy...")

form_result = calc_formation_energy(
    atoms=atoms, 
    e_mof=actual_e_mof, 
    ref_energies=refs
)

print(f"\n--- Formation Energy Results ---")
print(f"E_form per atom: {form_result.e_form_per_atom_ev} eV/atom")