process PREPARE_MANIFEST {
    publishDir "${params.outdir}/manifest", mode: 'copy', saveAs: { name -> name.tokenize('/').last() }
    input:
    path samples, stageAs: 'input_samples.tsv'
    path pairs, stageAs: 'input_pairs??.tsv'
    val base
    path bins, stageAs: 'pe150_bins.rds'
    val checksum
    path validator
    val temp_directory
    output:
    path 'validated/samples.tsv', emit: samples
    path 'validated/pairs.csv', emit: pairs
    path 'validated/expected_samples.txt', emit: expected
    path 'validated/cohort.json'
    script:
    // base may contain apostrophes; quote it as a shell argument, never as code.
    def quotedBase = "'" + base.replace("'", "'\"'\"'") + "'"
    def pairArg = pairs ? '--pairs input_pairs01.tsv' : ''
    def tempArg = temp_directory ? "--temp-directory '" + temp_directory.toString().replace("'", "'\"'\"'") + "'" : ''
    """
    python3 ${validator} --samples input_samples.tsv ${pairArg} ${tempArg} --base ${quotedBase} \\
      --pe150-bins pe150_bins.rds --pe150-sha256 ${checksum} --output validated
    """
    stub:
    // Manifest validation remains real even when scientific tasks are stubbed.
    def quotedBase = "'" + base.replace("'", "'\"'\"'") + "'"
    def pairArg = pairs ? '--pairs input_pairs01.tsv' : ''
    def tempArg = temp_directory ? "--temp-directory '" + temp_directory.toString().replace("'", "'\"'\"'") + "'" : ''
    """
    python3 ${validator} --development-stub --samples input_samples.tsv ${pairArg} ${tempArg} --base ${quotedBase} \\
      --pe150-bins pe150_bins.rds --pe150-sha256 ${checksum} --output validated
    """
}

process QDNASEQ_COHORT {
    container 'docker://huntsmanlab/qdnaseq:latest'
    cpus 16
    memory '32 GB'
    publishDir params.outdir, mode: 'copy'
    input:
    tuple val(ids), path(bams, stageAs: 'bam_inputs/*'), path(bais, stageAs: 'bam_inputs/*')
    path bins, stageAs: 'pe150_bins.rds'
    path runner
    path expected
    path checker
    output:
    path 'relative_cn/qdnaseq/pe/500kb/500kb_noXY_copyNumbersSegmented.rds', emit: segmented
    path 'relative_cn/qdnaseq/pe/500kb', emit: directory
    script:
    """
    mkdir -p relative_cn/qdnaseq/pe/500kb
    printf '%s\\n' ${bams.collect { "'${it}'" }.join(' ')} > bamfileslist.txt
    Rscript ${runner} 500kb ${task.cpus} relative_cn/qdnaseq/pe/500kb bamfileslist.txt ${bins}
    Rscript ${checker} relative_cn/qdnaseq/pe/500kb/500kb_noXY_copyNumbersSegmented.rds ${expected}
    """
    stub:
    """
    test \$(find bam_inputs -name '*.bam' | wc -l) -eq ${ids.size()}
    test \$(find bam_inputs -name '*.bai' | wc -l) -eq ${ids.size()}
    printf '%s\\n' ${bams.collect { "'${it}'" }.join(' ')} > staged_bams.txt
    mkdir -p relative_cn/qdnaseq/pe/500kb
    touch relative_cn/qdnaseq/pe/500kb/500kb_noXY_copyNumbersSegmented.rds
    """
}

process CGHCALL_COHORT {
    container 'docker://huntsmanlab/qdnaseq:latest'
    cpus 1
    memory '32 GB'
    publishDir "${params.outdir}/cghcall", mode: 'copy'
    input:
    path segmented
    path expected
    path runner
    path checker
    output:
    path 'cohort_500kb_noXY_CGHcall.rds', emit: called
    path 'cohort_500kb_noXY_CGHcall.rds.provenance.txt'
    script:
    """
    Rscript ${checker} ${segmented} ${expected}
    Rscript ${runner} --input-rds ${segmented} --output-rds cohort_500kb_noXY_CGHcall.rds \\
      --expected-count \$(wc -l < ${expected}) --expected-samples ${expected} --cohort cohort
    """
    stub:
    """
    test -f ${segmented}
    test -s ${expected}
    touch cohort_500kb_noXY_CGHcall.rds
    echo 'STUB ONLY: no scientific computation' > cohort_500kb_noXY_CGHcall.rds.provenance.txt
    """
}
