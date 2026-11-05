def shellQuote(value) {
    "'" + value.toString().replace("'", "'\"'\"'") + "'"
}

process SCORE_AND_AGGREGATE {
    container params.metrics_container
    cpus 1
    memory '8 GB'
    publishDir params.outdir, mode: 'copy', saveAs: { name ->
        name.endsWith('_results.tsv') ? name.tokenize('/').last() : name
    }
    input:
    path called, stageAs: 'cohort_500kb_noXY_CGHcall.rds'
    path samples, stageAs: 'samples.tsv'
    path pairs, stageAs: 'pairs.csv'
    path pfreq, stageAs: 'pfreq.csv'
    path helper, stageAs: 'clonality_helper.R'
    path preprocessing, stageAs: 'preprocessing.R'
    path matching, stageAs: 'matching.R'
    path fraction_implementation, stageAs: 'fraction_implementation.py'
    path runner
    path orchestrator
    path pcc_adapter
    path breakpoint_adapter
    val profile_location
    output:
    path 'metrics/sample_results.tsv', emit: samples
    path 'metrics/pair_results.tsv', emit: pairs
    path 'metrics/metric_provenance.json', emit: provenance
    path 'metrics/intermediate/*environment.txt', optional: true
    script:
    def resources = [pfreq: pfreq, helper: helper, preprocessing: preprocessing,
                     matching: matching, 'fraction-implementation': fraction_implementation]
        .findAll { key, value -> value }.collect { key, value -> "--${key} ${shellQuote(value)}" }.join(' ')
    """
    python3 ${shellQuote(orchestrator)} --called-rds ${called} --samples ${samples} --pairs ${pairs} \\
      --runner ${shellQuote(runner)} --pcc-adapter ${shellQuote(pcc_adapter)} --breakpoint-adapter ${shellQuote(breakpoint_adapter)} \\
      --rscript ${shellQuote(params.metrics_rscript)} --breakpoint-rscript ${shellQuote(params.breakpoint_rscript)} \\
      --profile-location ${shellQuote(profile_location)} --provenance-location metrics/metric_provenance.json ${resources} --output metrics
    """
    stub:
    """
    python3 ${shellQuote(orchestrator)} --stub --called-rds ${called} --samples ${samples} --pairs ${pairs} \\
      --profile-location ${shellQuote(profile_location)} --provenance-location metrics/metric_provenance.json --output metrics
    """
}

workflow PUBLIC_METRICS {
    take:
    called
    samples
    pairs
    profile_location
    main:
    pfreq = params.pfreq ? file(params.pfreq, checkIfExists: true) : []
    helper = params.llr_helper ? file(params.llr_helper, checkIfExists: true) : []
    preprocessing = params.breakpoint_preprocessing ? file(params.breakpoint_preprocessing, checkIfExists: true) : []
    matching = params.breakpoint_matching ? file(params.breakpoint_matching, checkIfExists: true) : []
    implementation = params.fraction_implementation ? file(params.fraction_implementation, checkIfExists: true) : []
    SCORE_AND_AGGREGATE(called, samples, pairs, pfreq, helper, preprocessing, matching, implementation,
        file(params.pcc_llr_runner, checkIfExists: true),
        file("${projectDir}/bin/run_metrics.py"), file("${projectDir}/bin/pcc_llr_adapter.R"),
        file("${projectDir}/bin/breakpoints_adapter.R"), profile_location)
    emit:
    sample_results = SCORE_AND_AGGREGATE.out.samples
    pair_results = SCORE_AND_AGGREGATE.out.pairs
}
