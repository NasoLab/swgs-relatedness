process ALIGNMENT {
    tag "Aligning ${sample_id}"
	container 'docker://blcdsdockerregistry/bwa-mem2_samtools-1.12:2.2.1'
	cpus 16
	memory '72 GB'
	scratch '/tmp'
    // time '36h'

    input:
    tuple val(sample_id), path(reads)
	path(ref_genome_directory, stageAs: 'reference')

    output:
    tuple val(sample_id), path("alignment_${sample_id}/${sample_id}.bwa.sorted.bam"), path("alignment_${sample_id}/${sample_id}.bwa.sorted.bai")

    script:
    def bwa_threads = Math.max(1, task.cpus - 4)
    def sort_threads = task.cpus - bwa_threads
    def sort_mem_mb = Math.max(1024, (task.memory.toMega() * 0.65 / sort_threads).intValue())
    def staged_reference = ref_genome_directory.resolve(file(params.reference_genome_path).name)

    """
    set -euo pipefail

    TMP_DIR=\$(mktemp -d "\${TMPDIR:-/tmp}/${sample_id}.bwa-sort.XXXXXX")
    trap 'rm -rf "\$TMP_DIR"' EXIT
    BAM_OUT="${sample_id}.bwa.sorted.bam"

    bwa-mem2 mem -M -t ${bwa_threads} '${staged_reference}' ${reads} -R '@RG\\tID:${sample_id}_ID\\tSM:${sample_id}\\tLB:${sample_id}_LB\\tPL:ILLUMINA' | \
        samtools sort -@ ${sort_threads} -m ${sort_mem_mb}M -T "\$TMP_DIR/${sample_id}" -o "\$BAM_OUT" -

    samtools index -@ 1 "\$BAM_OUT"
    mkdir -p "alignment_${sample_id}"
    mv "\$BAM_OUT" "alignment_${sample_id}/${sample_id}.bwa.sorted.bam"
    mv "\$BAM_OUT.bai" "alignment_${sample_id}/${sample_id}.bwa.sorted.bai"
    """      
    stub:
    def staged_reference = ref_genome_directory.resolve(file(params.reference_genome_path).name)
    """
    test -f '${reads[0]}'
    test -f '${reads[1]}'
    test -f '${staged_reference}'
    test -f '${staged_reference}.bwt.2bit.64'
    mkdir -p alignment_${sample_id}
    touch alignment_${sample_id}/${sample_id}.bwa.sorted.{bam,bai}
    """
}
