version 1.0

import "viral-pipelines/pipes/WDL/tasks/tasks_read_utils.wdl" as step_1
import "viral-pipelines/pipes/WDL/workflows/classify_single.wdl" as step_2
import "viral-pipelines/pipes/WDL/workflows/assemble_denovo.wdl" as step_3

workflow run {
    input {
        Array[File] files
        String library
        String sample
    }

    scatter (file in files) {
        call step_1.FastqToUBAM {
            input:            
                platform_name = "ILLUMINA",
                library_name = library,
                sample_name = sample,
                fastq_1 = file
        }
    }

    call step_2.classify_single {
        input:
            reads_bams =                          FastqToUBAM.unmapped_bam,
            emailAddress =   "example@email.com",
            spikein_db =                          "/gpfs20/scratch/gpk00003/20260717scratchPipeline/ERCC92.fa",
            trim_clip_db =                        "/gpfs20/scratch/gpk00003/20260717scratchPipeline/NexteraPE-PE.fa",
            kraken2_db_tgz =                      "/gpfs20/scratch/gpk00003/20260717scratchPipeline/k2_viral_20251015.tar.gz",
            krona_taxonomy_db_kraken2_tgz =       "/gpfs20/scratch/gpk00003/20260717scratchPipeline/KronaTools-2.8.1/taxonomy/taxonomy.tab",
            ncbi_taxdump_tgz =                    "/gpfs20/scratch/gpk00003/20260717scratchPipeline/new_taxdump.tar.gz"
    }
    
    Map[String, Array[String]] taxon_map = read_json("taxon_accessions.json")

    Array[String] accessions = taxon_map[classify_single.kraken2_top_taxon_id]

    scatter (acc in accessions) {
        String fasta = "refGenomes/" + acc + ".fasta"
    }

    Array[String] reference_genome_fastas = fasta

    call step_3.assemble_denovo {
        input:
            reads_unmapped_bams =       FastqToUBAM.unmapped_bam,
            reference_genome_fasta =    reference_genome_fastas,
            trim_clip_db =              "/gpfs20/scratch/gpk00003/20260717scratchPipeline/NexteraPE-PE.fa"
    }        
}

