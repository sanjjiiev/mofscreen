"""
Example 7: Volume Expansion Only (Step 4)
-----------------------------------------
Calculates structural swelling.
REQUIRES: Step 2 (Adsorption) to be completed with cell_opt=True.
"""
import os
from pathlib import Path
from ase.io import read
from mofscreen._core import calc_volume_expansion

cif_file = "test.cif"
out_dir = Path(os.getcwd()) / "results"
adsorption_out = out_dir / "adsorption.out"

# 1. Dependency Check
if not adsorption_out.exists():
    print("ERROR: Missing adsorption.out!")
    print("You must run '05_calc_adsorption_only.py' (with cell_opt=True) before calculating volume expansion.")
    exit(1)

# 2. Run Math
atoms = read(cif_file)
print("Parsing CP2K logs for Volume Expansion...")

vol_result = calc_volume_expansion(
    atoms=atoms, 
    out_dir=out_dir, 
    cell_opt=True, 
    ion_symbol="K"  # Ensure this matches the ion you used in Step 2!
)

print(f"\n--- Volume Expansion Results ---")
print(f"Initial Volume: {vol_result.v_before_A3:.2f} Å³")
if vol_result.v_after_A3:
    print(f"Final Volume  : {vol_result.v_after_A3:.2f} Å³")
    print(f"Expansion %   : {vol_result.expansion_pct:.2f}%")
else:
    print("Error: Could not extract final volume. Did you run Step 2 with cell_opt=True?")