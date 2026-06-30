This repository contains a workflow to identify the virus and the variant of the viruses contained within a human nasal swap sample, developed to be used in the lab of [Dr. Peter Stoilov](https://directory.hsc.wvu.edu/Profile/33977). 

The `runSamples.py` function is the most important one. It takes in a list of samples (which are folders that contain `.fastq.gz` files from an Illumina sequencer), schedules the workflow (in `full.wdl`), and produces a status table that updates when `status.sh` is ran. Outputs are put into the `0outputs` folder, grouped by the date and time that the samples were initially scheduled to be analyzed. More thorough documentation is available [here](https://docs.google.com/document/d/1WVVxAQP3dMMJQ7DezvK8sZAMv4Q8UES1vlBmU_fpy9Y/edit?tab=t.0). 

The bioinformatics algorithms come from [viral-pipelines](https://github.com/broadinstitute/viral-pipelines) from the Broad institute, which run WDL pipelines using [Cromwell](https://github.com/broadinstitute/cromwell). 

This code is ran on the [WVU Thorny Flat](https://docs.hpc.wvu.edu/text/83.ThornyFlat.html) computing cluster. As of June 2026, Thorny Flat uses Red Hat 7.9 (which has bash 4.2.46(2)), and has Python 3.9.18 and SLURM 23.11.4 available. Java JDK 17.0.1 and [Singularity](https://github.com/sylabs/singularity) 3.7.0 are available by using environment [modules](https://github.com/envmodules/modules).

A few additional files are obtained through submodules and from various sources:
\[ list out the sources \]
