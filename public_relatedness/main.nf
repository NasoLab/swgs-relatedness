nextflow.enable.dsl=2

// Resolve into a regular map: Nextflow params values are immutable once assigned.
def settings = new LinkedHashMap(params)
// Bundled paths are based on projectDir, never the launch or params-file directory.
def scientific = new groovy.json.JsonSlurper().parse(file("${projectDir}/scientific_sources.json").toFile()).sources
def referenceAssets = new groovy.json.JsonSlurper().parse(file("${projectDir}/references/manifest.json").toFile()).resources
def resourceDirectory = settings.resource_directory ?: System.getenv('SWGS_RESOURCE_DIR')
[runner: 'pcc_llr_runner', preprocessing: 'breakpoint_preprocessing', matching: 'breakpoint_matching',
 fraction_implementation: 'fraction_implementation'].each { source, key ->
    if (!settings[key]) settings[key] = "${projectDir}/${scientific[source].path}"
}
if (resourceDirectory) {
    referenceAssets.findAll { !it.suffix }.each { asset ->
        if (!settings[asset.config_param]) settings[asset.config_param] = "${resourceDirectory}/${asset.filename}"
    }
    if (!settings.llr_helper) settings.llr_helper = "${resourceDirectory}/${scientific.helper.filename}"
}
// Cohort-only sample QC needs the bundled runner, but no external pair model/helper.
if (!settings.pairs && !settings.called_rds) {
    settings.pfreq = null
    settings.llr_helper = null
}
if (!settings.metrics_container && settings.image_directory) settings.metrics_container = "${settings.image_directory}/metrics.sif"
if (!settings.metrics_rscript) settings.metrics_rscript = settings.metrics_container ? '/opt/swgs/bin/Rscript-llr' : 'Rscript-llr'
if (!settings.breakpoint_rscript) settings.breakpoint_rscript = settings.metrics_container ? '/opt/swgs/bin/Rscript-general' : 'Rscript-general'

def frozenSha256(path) {
    def digest = java.security.MessageDigest.getInstance('SHA-256')
    path.toFile().withInputStream { stream ->
        byte[] buffer = new byte[1024*1024]
        int n
        while ((n = stream.read(buffer)) > 0) digest.update(buffer, 0, n)
    }
    digest.digest().encodeHex().toString()
}

include { TRIMMOMATIC } from '../modules/local/trimmomatic'
include { ALIGNMENT } from '../modules/local/alignment' addParams(reference_genome_path: settings.reference)
include { MARK_DUPLICATES } from '../modules/local/mark_duplicates' addParams(output_directory: settings.outdir)
include { PREPARE_MANIFEST; QDNASEQ_COHORT; CGHCALL_COHORT } from './modules/cohort'
include { PUBLIC_METRICS } from './modules/metrics' addParams(settings)

workflow {
    if (!workflow.stubRun) {
        if (workflow.containerEngine != 'singularity') error 'FASTQ execution currently requires the singularity profile with validated local SIFs; no approved OCI digest is available'
        if (!settings.image_directory) error 'Supply image_directory in the execution-environment configuration; automatic pulls of latest tags are disabled'
        def runtimeImages = new groovy.json.JsonSlurper().parse(file("${projectDir}/environments/runtime_images.json").toFile()).images
        runtimeImages.each { image ->
            def path = file(image.role == 'metrics' ? settings.metrics_container : "${settings.image_directory}/${image.filename}", checkIfExists: true)
            if (frozenSha256(path) != image.sha256) error "Runtime image checksum mismatch: ${image.role}; use the recorded environment or validate a separately reviewed replacement"
        }
    }
    for (key in ['samples', 'reference', 'pe150_bins', 'pe150_bins_sha256', 'pcc_llr_runner']) {
        if (!settings[key]) error "Missing required ${key}; set resource_directory or supply the explicit reference path. See prepare_resources.py --help"
    }
    if (settings.paired_end != true || settings.crop_50 != false) {
        error 'Public relatedness requires paired-end reads without CROP:50'
    }
    if (settings.pairs) {
        for (key in ['pfreq', 'llr_helper', 'breakpoint_preprocessing', 'breakpoint_matching', 'fraction_implementation']) {
            if (!settings[key]) error "Missing ${key}; set resource_directory and run prepare_resources.py --resources DIRECTORY --fetch llr-helper --fetch pfreq. Supply PE150/indexes separately; see INSTALL.md"
            if (!file(settings[key]).exists()) error "Missing frozen ${key}: ${settings[key]}; use resource_directory and prepare_resources.py --help"
            file(settings[key], checkIfExists: true)
        }
    }
    def reference = file(settings.reference, checkIfExists: true)
    if (!(reference.name ==~ /[A-Za-z0-9_-][A-Za-z0-9_.-]*\.(fa|fasta|fna)/)) {
        error 'Use a reference basename containing letters, digits, dots, underscores or hyphens, ending in .fa/.fasta/.fna'
    }
    for (suffix in ['.0123', '.amb', '.ann', '.bwt.2bit.64', '.pac']) {
        file("${reference}${suffix}", checkIfExists: true)
    }
    if (!workflow.stubRun) {
        referenceAssets.findAll { it.config_param != 'pfreq' || settings.pairs }.each { asset ->
            def path = file("${settings[asset.config_param]}${asset.suffix}", checkIfExists: true)
            if (frozenSha256(path) != asset.sha256) error "Reference checksum mismatch: ${asset.id}; obtain the unchanged frozen asset using prepare_resources.py --help"
        }
        [runner: 'pcc_llr_runner', preprocessing: 'breakpoint_preprocessing', matching: 'breakpoint_matching',
         fraction_implementation: 'fraction_implementation'].each { key, param ->
            if (frozenSha256(file(settings[param], checkIfExists: true)) != scientific[key].sha256) error "Scientific source checksum mismatch: ${key}"
        }
        if (settings.pairs && frozenSha256(file(settings.llr_helper, checkIfExists: true)) != scientific.helper.sha256) error 'Inherited LLR helper checksum mismatch; acquire the exact frozen source'
    }
    def samples = file(settings.samples, checkIfExists: true)
    def pairs = settings.pairs ? [file(settings.pairs, checkIfExists: true)] : []
    def bins = file(settings.pe150_bins, checkIfExists: true)
    if (!(settings.pe150_bins_sha256 ==~ /[a-fA-F0-9]{64}/)) error 'Invalid PE150 SHA256'

    PREPARE_MANIFEST(samples, pairs, samples.parent.toString(), bins, settings.pe150_bins_sha256,
        file("${projectDir}/bin/prepare_manifest.py"), settings.temp_directory ?: '')
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
    if (!workflow.stubRun && settings.metrics_container) {
        def image = file(settings.metrics_container, checkIfExists: true)
        if (frozenSha256(image) != 'ae7c40c285c19a6db6d01bb61f839cdd348f4cfd3f7510ae533091e2ed9f7151') error 'Metrics SIF checksum mismatch; validate a separately reviewed replacement before use'
    }
    for (key in ['called_rds', 'validated_samples', 'validated_pairs', 'pcc_llr_runner']) {
        if (!settings[key]) error "CACHED_METRICS requires --${key}"
    }
    PUBLIC_METRICS(Channel.value(file(settings.called_rds, checkIfExists: true)),
        Channel.value(file(settings.validated_samples, checkIfExists: true)),
        Channel.value(file(settings.validated_pairs, checkIfExists: true)), file(settings.called_rds).toAbsolutePath().toString())
}
