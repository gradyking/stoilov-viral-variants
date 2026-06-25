#!/usr/bin/env python3
# post-workflow tasks using the metadata.json
# move the output files in moveOutputsList.txt to the 0outputs folder that the metadata.json file is located in
#     if the workflow doesn't complete properly, it still attempts to move the Krona plot
# write to status.tsv

import os
import sys
import json
from pathlib import Path
from status_utils import update_status
from datetime import datetime

def subtract_times(t1, t2):
    # convert from string formatted like 2026-06-24T16:25:06.835Z to 2026-06-24T16:25:06.835+00:00 to be within the datetime iso standard
    t1 = datetime.fromisoformat(t1.replace("Z", "+00:00"))
    t2 = datetime.fromisoformat(t2.replace("Z", "+00:00"))
    delta = t1 - t2
    
    total_seconds = int(delta.total_seconds())
    hours, remainder = divmod(total_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    
    return(f"{hours:02}:{minutes:02}:{seconds:02}")

# Safe symlink creation function from here https://zetcode.com/python/os-symlink/
def create_symlink(src, dst):
    try:
        os.symlink(src, dst)
    except FileExistsError:
        if os.path.islink(dst):
            print(f"Symlink {dst} already exists")
            # Optionally update existing symlink
            # os.remove(dst)
            # os.symlink(src, dst)
            # print(f"Updated {dst} to point to {src}")
        # else:
            # print(f"{dst} exists but isn't a symlink")

def main():
    if len(sys.argv) < 1:
        sys.exit(
            "Usage: python step4.py [metadata.json path]"
        )

    metadata_file = Path(sys.argv[1])

    # the output files should be placed in the same folder as the metadata.json
    output_dir = metadata_file.parents[0] / "workflow_outputs"
    output_dir.mkdir(exist_ok=True)
    
    # find sample name to be passed into update_status
    sample_name = metadata_file.parents[0].name
    status_tsv = metadata_file.parents[1] / "status.tsv"

    with open('moveOutputsList.txt', 'r') as file:
        # remove comments and empty lines from from file
        desired_outputs = [line.strip() for line in file if (not line.startswith("#") and line.strip() != "")]

    print(desired_outputs)     

    with open(metadata_file, 'r') as file:
        metadata = json.load(file)

    # find pipeline execution time
    execution_time = subtract_times(metadata['end'], metadata['start'])

    # if the overall pipeline fails (for example, there is no top taxon found, or there aren't enough reads for assemble_denovo)
    # the outputs are not put into the "outputs" key in the metadata.json
    # so instead i can go within the classify_single call and just pull the Krona plot directly from there, which normally illustrates whatever problem happened pretty well
    if len(metadata['outputs']) == 0:
        print("overall pipeline failed, attempting to move Krona plot to output")
        try:
            update_status(status_tsv, sample_name, "finished with error in assemble_denovo", execution_time)
            create_symlink(metadata['calls']['run.classify_single'][0]['outputs']['kraken2_krona_plot'], output_dir / "kraken2_krona_plot.html")
        except:
            update_status(status_tsv, sample_name, "errored out on classify_single", execution_time)
            raise Exception("classify_single had an issue while running. check stdout.txt and/or stderr.txt")
    else:
        for output in desired_outputs:
            print(output)

            try:
                json_query = metadata['outputs'][output]
            except:
                print(f"output {output} not found, skipping")
                continue
        
            # some outputs are just a number, so for those i make a .txt file
            if isinstance(json_query, int) or isinstance(json_query, float):
                with open(output_dir / (output + ".txt"), "w+") as file:
                    file.write(str(output))
                    print(f'created file for {output}')
            else:
                # query the .json to find where a given output is located on disk
                
                original_file = Path(json_query)
        
                # find file extension
                original_file_extension = os.path.splitext(original_file)[1]
                # print(original_file_extension)        
        
                # append the desired output name plus the correct file extension to the destination folder
                new_dir = output_dir / (output + original_file_extension)
        
                # create a simlink between the original file location and the new location
                create_symlink(original_file, new_dir)
        
                print(f"created symlink for {output}")
        
        update_status(status_tsv, sample_name, "finished", execution_time)

main()
