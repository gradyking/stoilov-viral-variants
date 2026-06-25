#!/usr/bin/env python3

# Written by Grady King, mostly by ChatGPT w/ manual modifications Feb 2026
# Takes in a .tsv file (such as https://github.com/broadinstitute/viral-references/blob/main/assembly/reference_genomes.tsv), 
# converting from NCBI taxon_ids to genome accession numbers and downloads the resulting genome in .fasta format using the viral-phylo image from Broad institute
# it also makes a taxon_acccessions.json file converting between taxon_ids and the accession numbers, for use in a WDL pipeline

import csv
import sys
import subprocess
import json
from pathlib import Path
from collections import defaultdict

SIF_PATH = "../broadDockers/viral-phylo.sif"
BATCH_SIZE = 100
JSON_FILENAME = "taxon_accessions.json"


def chunk_list(data, size):
    """Split a list into chunks of a specified size."""
    return [data[i:i + size] for i in range(0, len(data), size)]


def parse_accessions(tsv_path):
    """
    Extract colon-separated accessions from the last column of a TSV.
    Returns:
        accessions_flat: list of all accessions
        taxon_dict: dict of taxon_id -> list of accessions (merged if multiple rows)
    """
    accessions_flat = []
    taxon_dict = defaultdict(list)

    with open(tsv_path, newline="") as f:
        reader = csv.reader(f, delimiter="\t")
        for row in reader:
            if not row:
                continue

            taxon_id = row[0].strip()
            last_col = row[-1].strip()
            if last_col:
                accessions = last_col.split(":")
                accessions_flat.extend(accessions)
                taxon_dict[taxon_id].extend(accessions)

    # Optionally, remove duplicates per taxon
    taxon_dict = {k: list(dict.fromkeys(v)) for k, v in taxon_dict.items()}

    return accessions_flat, taxon_dict


def run_command(command_string):
    """Run a shell command through bash -lc so module load works."""
    print(f"\n[RUNNING] {command_string}\n")
    result = subprocess.run(["bash", "-lc", command_string])
    if result.returncode != 0:
        sys.exit(f"Command failed with exit code {result.returncode}")


def main():
    if len(sys.argv) != 3:
        sys.exit(
            "Usage: python run_ncbi_fasta_batches.py reference_genomes.tsv email@example.com"
        )

    tsv_path = sys.argv[1]
    email = sys.argv[2]

    accessions, taxon_dict = parse_accessions(tsv_path)

    if not accessions:
        sys.exit("No accession numbers found.")

    # Write merged JSON file
    with open(JSON_FILENAME, "w") as jf:
        json.dump(taxon_dict, jf, indent=2)
    print(f"Wrote merged taxon → accessions mapping to {JSON_FILENAME}")

    print(f"Total accessions: {len(accessions)}")

    # Ensure output directory exists
    Path("refGenomes").mkdir(exist_ok=True)

    batches = chunk_list(accessions, BATCH_SIZE)

    for i, batch in enumerate(batches, start=1):
        print(f"\n=== Processing batch {i}/{len(batches)} ({len(batch)} accessions) ===")

        accession_str = " ".join(batch)

        cmd = f"""
module load singularity
singularity exec {SIF_PATH} ncbi.py fetch_fastas \
    {email} \
    refGenomes/ \
    {accession_str} \
    --forceOverwrite \
    --loglevel DEBUG
"""

        run_command(cmd)


if __name__ == "__main__":
    main()

