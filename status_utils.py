import csv
import fcntl

# update the status of a given sample in the status.tsv, with file locks
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

