#!/usr/bin/env python3

import os
import sys
import subprocess
import json
import time
from datetime import datetime
from pathlib import Path
import csv
import fcntl

def main():
    
    # remove "runSamples.py" from args, the rest are samples
    samples = sys.argv[1:]
    # print(samples)

    # find the w parameter, and if it exists, change the wdl_name param to the passed filename
    wdl_name = "full.wdl"
    if "-w" in samples:
        w_index = samples.index("-w")
        wdl_name = samples[w_index + 1]
        del samples[w_index:w_index + 2]

    # check if they gave all valid folders for samples and a valid wdl_name
    # print(list(os.path.isdir(d) for d in samples))
    exit = 0
    if len(sys.argv) < 2:
        exit = 1
        print("please specify at least one sample folder name")
    if not all(os.path.isdir(d) for d in samples):
        exit = 1
        print("please make sure all samples provided are valid directories")
    if not os.path.isfile(wdl_name):
        exit = 1
        print("please make sure the provided .wdl is a valid file")
    if exit:
        sys.exit("Usage: python runSamples.py -w [.wdl name] [sample folder names]")

    # find the time and all unique names of parent folders to name the output folder
    current_time = datetime.now().strftime("%Y-%m-%d_%H:%M:%S")
    parents = "_".join(set([Path(d).parent.name for d in samples]))

    output_parent = f"0outputs/{current_time}_{parents}"
    os.makedirs(output_parent)
    
    scheduled_samples = list()
    for sample in samples:
        path = Path(sample)
        sample_name = path.name
        library_name = path.parent.name

        # find all lanes within the folder
        folder_pattern = f"{sample_name}_L*"

        # find matching folders
        folders = [p for p in path.glob(folder_pattern) if p.is_dir()]

        fastq_files = list()

        for folder in sorted(folders):
            files = sorted(str(f.resolve()) for f in folder.rglob("*.fastq.gz")) # find all fastq.gz files in each folder and resolve to full paths
            fastq_files.extend(files)

        inputDict = dict()
        inputDict["run.files"] = fastq_files
        inputDict["run.library"] = library_name
        inputDict["run.sample"] = sample_name

        # skip samples without any files
        if len(fastq_files) < 1:
            print(sample_name + " has no .fastq.gz files. Skipping...")
            continue

        # construct output path and make sure it exists. currently have it grouped by original time that runSamples.py is called
        output_path = f"{output_parent}/{sample_name}"
        os.makedirs(output_path, exist_ok=True)

        with open(f"{output_path}/input.json", "w") as jf:
            json.dump(inputDict, jf, indent=2)

        # schedule call to full.wdl with sbatch through stdin
        job_script = f"""#!/bin/bash
        #SBATCH
        module load singularity
        module load lang/java/jdk-17.0.1

        python step0.py "{sample_name}" "{output_parent}/status_log.tsv"
        
        java -Dconfig.file=cromwellWithSingularity.conf \
            -jar cromwell-88.jar run \
            --inputs "{output_path}/input.json" \
            --metadata-output "{output_path}/metadata.json" \
        {wdl_name}

        python step4.py "{output_path}/metadata.json"
        """

        result = subprocess.run(
            [
                "sbatch",
                "-c", "8",
                "-t", "2:00:00",
                "--mem=90G",
                f'--job-name={sample_name}_pipeline',
                "-o", f"{output_path}/stdout.txt",
                "-e", f"{output_path}/stderr.txt",
            ],
            input=job_script,
            text=True,
            capture_output=True
        )

        print(f"Scheduled {sample_name}_{current_time}" + " -- " + result.stdout.rstrip()) #remove newline at end of stdout
        scheduled_samples.append(sample_name)

        with open(f"{output_parent}/status_log.tsv", 'a', newline='') as f:
            fcntl.flock(f, fcntl.LOCK_EX)

            # write info about scheduled sample to the .tsv
            writer = csv.writer(f, delimiter='\t')
            writer.writerow([datetime.now().isoformat(), sample_name, "scheduled", None])

            # release the file lock
            fcntl.flock(f, fcntl.LOCK_UN)
        
        # prevent submitting all jobs instantly
        time.sleep(0.2)

    # find current path to pass to script
    current_path = sys.path[0]

    # create a bash script that will print status.tsv in a pretty way
    # this bash script is constructed weirdly, because it can be run from any directory
    # the SCRIPT_DIR gets the local directory for the bash script (which also contains the status_log.tsv and the status.tsv that gets made)
    # the python code adds the current_path (which also contains status_utils.py) then imports it and passes in the path local to the bash script to the status table function
    # to have the $SCRIPT_DIR actually replace itself in the python command, i used https://stackoverflow.com/questions/840536/how-to-use-an-environment-variable-inside-a-quoted-string-in-bash#comment58143383_9420853
    with open(f"{output_parent}/status.sh", "w") as f:
        f.writelines("\n".join(
         ["#!/bin/bash", 
          "",
          "# get bash local directory https://stackoverflow.com/a/246128",
          "SCRIPT_DIR=$(cd -- \"$(dirname -- \"${BASH_SOURCE[0]}\")\" &>/dev/null && pwd)",
          "",
          "# run python script to generate status.tsv",
         f"python -c 'import sys; sys.path.append(\"{current_path}\"); import status_utils; status_utils.construct_status_table_from_log(\"'\"$SCRIPT_DIR\"'/status_log.tsv\")'",
          "column -t -s $'\t' \"$SCRIPT_DIR/status.tsv\""]))

    # https://stackoverflow.com/a/33179977 make status executable (+x)
    os.chmod(f"{output_parent}/status.sh", os.stat(f"{output_parent}/status.sh").st_mode | 0o111)

    print(f"To print status table, run:\n{output_parent}/status.sh")

if __name__ == "__main__":
    main()

