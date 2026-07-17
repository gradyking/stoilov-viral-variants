import csv
import fcntl
from datetime import datetime
from pathlib import Path
# this contains misc functions for dealing with the status tables

# appends a row to the status log for each step. appending prevents race conditions and allows for interlacing between different processes
def add_status_log(status_log_path, sample_name, status, execution_time=None):
    with open(status_log_path, "a") as f:
        fcntl.flock(f, fcntl.LOCK_EX) # file lock prevents multiple writes at the same time

        try:
            writer = csv.writer(f, delimiter = '\t')
            writer.writerow([datetime.now().isoformat(), sample_name, status, execution_time])

        finally:
            fcntl.flock(f, fcntl.LOCK_UN)

# a status that contains "finished" is highest priority, then "error", then "running", then "scheduled"
def assign_priority(status):
    if "finish" in status.lower():
        return 4
    elif "error" in status.lower():
        return 3
    elif "running" in status.lower():
        return 2
    elif "scheduled" in status.lower():
        return 1
    else:
        return 0

#  converting from the status log to a nicely formatted table
def construct_status_table_from_log(status_log_path):
    # find path for status.tsv to live
    status_table_path = Path(status_log_path).parents[0] / "status.tsv"

    # from status log, create a dictionary of statuses keyed by sample
    samples = dict()
    with open(status_log_path, 'r') as f:
        reader = csv.reader(f, delimiter = '\t')
        reads = list(reader)
        for row in reads:
            # sometimes execution_time is used, other times it isn't (like when execution hasn't happened yet)
            if(len(row) == 4):
                timestamp, sample_name, status, execution_time = row
            else:
                timestamp, sample_name, status = row
                execution_time = None
            
            if sample_name not in samples.keys():
                samples[sample_name] = [(timestamp, status, execution_time),]
            else:
                samples[sample_name].append((timestamp, status, execution_time))

    # for each sample, need to find the most pertinent message to display, which should be the message that is furthest along the process
    # i could just take the last status, but i see a world where there is a minor race condition between when a sample is scheduled versus when it starts running
    # so i prioritize it by the words in the status
    output_status_table = list()
    error = 0 # this is to add a helpful message at the bottom if any errors occur
    for sample_name in sorted(samples.keys()):

        # isolate statuses
        statuses = [x[1] for x in samples[sample_name]]

        # update error if "error" is found in any status for any sample
        if any(["error" in status for status in statuses]) and error == 0:
            error = 1

        # find highest priority status for the given sample (includes ties)
        priority = [assign_priority(x) for x in statuses]
        highestPriorityIndices = [i for i, x in enumerate(priority) if x == max(priority)]
        
        # the only scenario that might have multiple with the same priority would be multiple errors.
        # i'll take the latest timestamp, concatenate the error messages, and take the latest execution_time
        # for the others, i'll just take the last timestamp and last execution_time listed
        timestamp = samples[sample_name][highestPriorityIndices[-1]][0]
        status = " | ".join([x for i, x in enumerate(statuses) if i in highestPriorityIndices]) # slices statuses list by highestPriorityIndices, then joins them with |
        execution_time = samples[sample_name][highestPriorityIndices[-1]][2]

        # print(f"{sample_name}, {timestamp}, {status}, {execution_time}")
        output_status_table.append((sample_name, timestamp, status, execution_time))

    # write TSV to the status_table_path, to be further formatted by the linux column function when printed
    with open(status_table_path, 'w') as f:
        writer = csv.writer(f, delimiter = '\t')
        writer.writerow(["sample_name", "timestamp", "status", "execution_time"])
        for row in output_status_table:
            # print(row)
            writer.writerow(row)
        # if at least one status message mentions an error, I put this message at the bottom of the status table as advice for what to look for
        if error:
            writer.writerow(["at least one sample has an error. some are relatively innocuous (i.e. no top taxon was found), "
"but some aren't. to investigate, I recommend reading the Finding Errors entry on the wiki",])
