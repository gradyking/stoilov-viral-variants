import csv
import fcntl
from datetime import datetime
from pathlib import Path

# update the status of a given sample in the status.tsv, with file locks
# deprecated due to bad race dependencies
def update_status(status_tsv, sample_name, status, execution_time=None):

    # open the table, lock it so other executions can't also read/write to it
    # update the corresponding row, then write to the file and release the lock
    # lock is necessary since multiple processes are writing to one file
    with open(status_tsv, "r+", newline="") as f:
        fcntl.flock(f, fcntl.LOCK_EX)

        try:
            f.seek(0) # weird fix for when a file cursor isn't at the beginning of the file for some reason? i don't really fully understand this tbh
            reader = csv.reader(f, delimiter='\t')
            headers = next(reader)
            rows = list(reader)
    
            # find row with correct sample_name
            for i, row in enumerate(rows):
                if row[0] == sample_name:
                    rows[i] = [sample_name, status, execution_time]
                    break
            
            # return to beginning of file
            f.seek(0)
            f.truncate()
    
            # write table with updated row, with file locks to prevent two programs both trying to write to it
            writer = csv.writer(f, delimiter = '\t')
            writer.writerow(["sample_name", "status", "execution_length"])
            writer.writerows(rows)

        finally:
            fcntl.flock(f, fcntl.LOCK_UN)

# appending a row is far safer
def add_status_log(status_log_path, sample_name, status, execution_time=None):
    with open(status_log_path, "a") as f:
        fcntl.flock(f, fcntl.LOCK_EX)

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

# need to write a function for converting from the status log to the nicely formatted table that i had before from the TSV
def construct_status_table_from_log(status_log_path):
    print('ahhhh')
    status_table_path = Path(status_log_path).parents[0] / "status.tsv"
    output_status_table = list()

    samples = dict()
    with open(status_log_path, 'r') as f:
        reader = csv.reader(f, delimiter = '\t')
        reads = list(reader)
        for row in reads:
            timestamp, sample_name, status = row
            
            if(len(row) == 4):
                execution_time = row[3]
            else:
                execution_time = None
                
            if sample_name not in samples.keys():
                samples[sample_name] = [(timestamp, status, execution_time),]
            else:
                samples[sample_name].append((timestamp, status, execution_time))

    print('read')

    for sample_name in sorted(samples.keys()):
        statuses = [x[1] for x in samples[sample_name]]
        priority = [assign_priority(x) for x in statuses]
        highestPriorityIndices = [i for i, x in enumerate(priority) if x == max(priority)]
        # the only scenario that might have mutiple with the same priority would be multiple errors.
        # i'll take the latest timestamp, concatenate the error messages, and take the latest execution_time
        timestamp = samples[sample_name][highestPriorityIndices[-1]][0]
        status = " | ".join([x for i, x in enumerate(statuses) if i in highestPriorityIndices]) # slices statuses list by highestPriorityIndices, then joins them with |
        execution_time = samples[sample_name][highestPriorityIndices[-1]][2]

        print(f"{sample_name}, {timestamp}, {status}, {execution_time}")
        output_status_table.append((sample_name, timestamp, status, execution_time))

    with open(status_table_path, 'w') as f:
        writer = csv.writer(f, delimiter = '\t')
        writer.writerow(["sample_name", "timestamp", "status", "execution_time"])
        for row in output_status_table:
            print(row)
            writer.writerow(row)
