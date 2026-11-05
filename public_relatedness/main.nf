nextflow.enable.dsl=2

include { TRIMMOMATIC } from '../modules/local/trimmomatic'
include { ALIGNMENT } from '../modules/local/alignment' addParams(reference_genome_path: params.reference)
include { MARK_DUPLICATES } from '../modules/local/mark_duplicates' addParams(output_directory: params.outdir)
include { PREPARE_MANIFEST; QDNASEQ_COHORT; CGHCALL_COHORT } from './modules/cohort'
include { PUBLIC_METRICS } from './modules/metrics'

workflow {
    for (key in ['samples', 'reference', 'pe150_bins', 'pe150_bins_sha256', 'pcc_llr_runner']) {
        if (!params[key]) error "Missing required parameter --${key}"
    }
    if (params.paired_end != true || params.crop_50 != false) {
        error 'Public relatedness requires paired-end reads without CROP:50'
    }
    if (params.pairs) {
        for (key in ['pfreq', 'llr_helper', 'breakpoint_preprocessing', 'breakpoint_matching', 'fraction_implementation']) {
            if (!params[key]) error "Pair scoring requires --${key} with the frozen resource"
            file(params[key], checkIfExists: true)
        }
    }
    def reference = file(params.reference, checkIfExists: true)
    if (!(reference.name ==~ /[A-Za-z0-9_-][A-Za-z0-9_.-]*\.(fa|fasta|fna)/)) {
        error 'Use a reference basename containing letters, digits, dots, underscores or hyphens, ending in .fa/.fasta/.fna'
    }
    for (suffix in ['.0123', '.amb', '.ann', '.bwt.2bit.64', '.pac']) {
        file("${reference}${suffix}", checkIfExists: true)
    }
    def samples = file(params.samples, checkIfExists: true)
    def pairs = params.pairs ? [file(params.pairs, checkIfExists: true)] : []
    def bins = file(params.pe150_bins, checkIfExists: true)
    if (!(params.pe150_bins_sha256 ==~ /[a-fA-F0-9]{64}/)) error 'Invalid PE150 SHA256'

    PREPARE_MANIFEST(samples, pairs, samples.parent.toString(), bins, params.pe150_bins_sha256,
        file("${projectDir}/bin/prepare_manifest.py"), params.temp_directory ?: '')
    expected = PREPARE_MANIFEST.out.samples.splitCsv(header: true, sep: '\t').collect()
    fastqs = expected.flatMap { rows -> rows.collect { row ->
        tuple(row.sample_id, [file(row.fastq_1, checkIfExists: true), file(row.fastq_2, checkIfExists: true)])
    } }
    TRIMMOMATIC(fastqs)
    trimmed = TRIMMOMATIC.out.map { id, reads ->
        def mates = ['.f.paired.fastq.gz', '.r.paired.fastq.gz'].collect { suffix ->
            def found = reads.findAll { it.name.endsWith(suffix) }
            if (found.size() != 1) error "Expected exactly one ${suffix} for ${id}"
            found[0]
        }
        tuple(id, mates)
    }
    ALIGNMENT(trimmed, Channel.value(reference.parent))
    MARK_DUPLICATES(ALIGNMENT.out.map { id, bam, bai -> tuple(id, bam) })
    // A single cohort barrier: no per-pair calling and no dropped failed samples.
    // combine concatenates list values; wrap collections in maps to retain arity.
    cohort = MARK_DUPLICATES.out[0].collect(flat: false).map { [completed: it] }
        .combine(expected.map { [rows: it] }).map { aligned, manifest ->
        def completed = aligned.completed
        def rows = manifest.rows
        def ids = rows.collect { it.sample_id }
        def observed = completed.collect { it[0] }
        if (observed.size() != observed.unique(false).size() || observed.toSet() != ids.toSet()) {
            error 'Incomplete/conflicting cohort: missing or extra alignment samples'
        }
        def ordered = ids.collect { id -> completed.find { it[0] == id } }
        tuple(ids, ordered.collect { it[1] }, ordered.collect { it[2] })
    }
    QDNASEQ_COHORT(cohort, Channel.value(bins),
        file("${projectDir}/../bin/runQDNAseq.R"), PREPARE_MANIFEST.out.expected,
        file("${projectDir}/bin/assert_cohort.R"))
    CGHCALL_COHORT(QDNASEQ_COHORT.out.segmented, PREPARE_MANIFEST.out.expected,
        file("${projectDir}/../bin/prepare_cghcall_cohort.R"),
        file("${projectDir}/bin/assert_cohort.R"))
    PUBLIC_METRICS(CGHCALL_COHORT.out.called, PREPARE_MANIFEST.out.samples, PREPARE_MANIFEST.out.pairs,
        'cghcall/cohort_500kb_noXY_CGHcall.rds')
}

// Cached called profiles only: no alignment, normalization or calling is invoked.
workflow CACHED_METRICS {
    for (key in ['called_rds', 'validated_samples', 'validated_pairs', 'pcc_llr_runner']) {
        if (!params[key]) error "CACHED_METRICS requires --${key}"
    }
    PUBLIC_METRICS(Channel.value(file(params.called_rds, checkIfExists: true)),
        Channel.value(file(params.validated_samples, checkIfExists: true)),
        Channel.value(file(params.validated_pairs, checkIfExists: true)), file(params.called_rds).toAbsolutePath().toString())
}
