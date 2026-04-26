"""
Example 2: Advanced Potassium Screening
---------------------------------------
This script tests a MOF for Potassium-ion battery suitability.
It inserts 4 Potassium ions and allows the CP2K optimizer to relax 
the cell volume to calculate exact structural expansion.
"""
from mofscreen import run_screening

print("Starting advanced MOF screening for Potassium (K)...")

results = run_screening(
    cif_path="test.cif",
    ion_symbol="K",        # Switch the target ion to Potassium
    n_ions=4,              # Find the 4 largest void sites and insert K
    num_cores=16,
    cell_opt=True,         # Turn on volume relaxation (CELL_OPT)
    compute_refs=True      # Dynamically compute elemental reference energies
)

print("\n--- Potassium Storage Results ---")
if results.volume.expansion_pct is not None:
    print(f"Volume Expansion after loading 4K: {results.volume.expansion_pct:.2f}%")
else:
    print("Volume calculation failed or was skipped.")

if results.formation.e_form_per_atom_ev is not None:
    print(f"Thermodynamic Stability (E_form): {results.formation.e_form_per_atom_ev:.3f} eV/atom")