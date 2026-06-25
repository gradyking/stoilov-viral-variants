#!/usr/bin/env python3
# pre-workflow tasks:
# update status.tsv that the workflow is running with the time that it started

import sys
from status_utils import update_status
from datetime import datetime

def main():
    if len(sys.argv) < 1:
        sys.exit(
            "Usage: python step0.py [sample name] [status_tsv path]"
        )

    sample_name = sys.argv[1]
    status_tsv = sys.argv[2]

    now = datetime.now()
    update_status(status_tsv, sample_name, "running", f"started {now.hour:02}:{now.minute:02}:{now.second:02}")

main()
