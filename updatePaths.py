#!/usr/bin/env python3
# replace the file paths in cromwellWithSingularity.conf and full.wdl to be relative to the local file system
# also replaces the email address in full.wdl

#!/usr/bin/env python3

from pathlib import Path
import argparse
import re

parser = argparse.ArgumentParser()
parser.add_argument("email", help="Email address to use in full.wdl")
args = parser.parse_args()

email = args.email

# Directory containing this script
current_directory = Path(__file__).resolve().parent

# ----------------------------------------------------------------------
# Update cromwellWithSingularity.conf
# ----------------------------------------------------------------------

conf_file = current_directory / "cromwellWithSingularity.conf"

with open(conf_file, "r") as f:
    lines = f.readlines()

new_lines = []
for line in lines:
    if "cromwellWithSingularityDockerManip.sh" in line:
        indent = re.match(r"^\s*", line).group(0)
        new_lines.append(
 #           f'{indent}docker-manip-script = "{current_directory}/cromwellWithSingularityDockerManip.sh"\n'
            f'{indent}{current_directory}/cromwellWithSingularityDockerManip.sh ' + '${docker} ${cwd} ${docker_cwd} ${job_shell} ${docker_script}\n'
            
        )
    else:
        new_lines.append(line)

with open(conf_file, "w") as f:
    f.writelines(new_lines)

# ----------------------------------------------------------------------
# Update full.wdl
# ----------------------------------------------------------------------

wdl_file = current_directory / "full.wdl"

with open(wdl_file, "r") as f:
    text = f.read()

# Extract existing k2 filename from WDL
k2_match = re.search(r'"([^"]*k2_viral_\d+\.tar\.gz)"', text)
if not k2_match:
    raise RuntimeError("Could not find k2_viral database in full.wdl")

k2_filename = Path(k2_match.group(1)).name

replacements = {
    "ERCC92.fa": current_directory / "ERCC92.fa",
    "NexteraPE-PE.fa": current_directory / "NexteraPE-PE.fa",
    "taxonomy.tab": current_directory / "KronaTools-2.8.1" / "taxonomy" / "taxonomy.tab",
    "new_taxdump.tar.gz": current_directory / "new_taxdump.tar.gz",
    k2_filename: current_directory / k2_filename,
}

# find patterns like "/scratch/gpk00003/20260717scratchPipeline/ERCC92.fa" or "/home/me/files/ERCC92.fa"
# and replaces them with "{new_path}/ERCC92.fa"
for filename, new_path in replacements.items():
    text = re.sub(
        rf'"[^"]*{re.escape(filename)}"',
        f'"{new_path}"',
        text,
    )

with open(wdl_file, "w") as f:
    f.write(text)

print("Updated cromwellWithSingularity.conf")
print("Updated full.wdl")
