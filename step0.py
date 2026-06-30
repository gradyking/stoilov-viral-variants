#!/usr/bin/env python3
# pre-workflow tasks:
# update status_log.tsv that the workflow is running with the time that it started

import sys
from status_utils import add_status_log
from datetime import datetime

def main():
    if len(sys.argv) < 1:
        sys.exit(
            "Usage: python step0.py [sample name] [status_tsv path]"
        )

    sample_name = sys.argv[1]
    status_log_tsv = sys.argv[2]

    now = datetime.now()
    add_status_log(status_log_tsv, sample_name, "running", None)
    print(f'add_status_log took {datetime.now() - now}')
main()
