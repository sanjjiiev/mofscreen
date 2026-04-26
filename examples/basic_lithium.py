"""
Example 1: Basic Lithium Screening
----------------------------------
This script runs the standard 4-step CP2K pipeline (Bandgap, Adsorption, 
Formation, and Volume Expansion) for a single Lithium ion.
"""
import os
from mofscreen import run_screening

# Make sure you have a test.cif file in the same directory!
cif_file = "test.cif"

if not os.path.exists(cif_file):
    print(f"Please place a valid {cif_file} in this directory to run the example.")
    exit(1)

print("Starting basic MOF screening for Lithium...")

# Run the pipeline
results = run_screening(
    cif_path=cif_file,
    ion_symbol="Li",       # Default ion
    n_ions=1,              # Insert 1 ion
    num_cores=16,          # Number of CPU cores to use
    fast_mode=True         # Lowers CP2K cutoffs for faster testing
)

print("\n--- Quick Extraction ---")
print(f"MOF Formula: {results.formula}")
print(f"Bandgap    : {results.bandgap.bandgap_ev:.3f} eV")
print(f"Li E_ads   : {results.adsorption.e_ads_ev:.3f} eV")