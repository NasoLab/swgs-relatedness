process MARK_DUPLICATES {
	tag "marking duplicates reads in $sample_id"
	publishDir params.output_directory, mode:'copy'
	container 'docker://broadinstitute/picard@sha256:de4d1f713e6b42ac3cb7b74a68174f00f7fdba8366eedcd13a30b242625a10c5'
	cpus 1
	memory '128 G'
	scratch '/tmp'
	// time '12h'

	input:
	tuple val(sample_id), path(bam)

	output:
	tuple val(sample_id), path("alignment_outputs/${sample_id}/${sample_id}.*bwa.sorted.mkdup.bam"), path("alignment_outputs/${sample_id}/${sample_id}.*bwa.sorted.mkdup.bai"), path("alignment_outputs/${sample_id}/${sample_id}.markdups_metrics.txt")
	path("alignment_outputs/${sample_id}/${sample_id}.*bwa.sorted.mkdup.bam")
	path("alignment_outputs/${sample_id}/${sample_id}.markdups_metrics.txt"), emit: log

	script:
	"""
	set -euo pipefail

	TEMP=\$(mktemp -d "\${TMPDIR:-/tmp}/${sample_id}.markdup.XXXXXX")
	trap 'rm -rf "\$TEMP"' EXIT
    mkdir -p "alignment_outputs/${sample_id}"

	if [ ${params.paired_end} = true ]; then

    	if [ ${params.crop_50} = true ]; then
        	java -Xmx${task.memory.toGiga() - 1}g -XX:-UsePerfData -Djava.io.tmpdir="\$TEMP" -jar /usr/picard/picard.jar MarkDuplicates \
            	--INPUT ${bam} \
            	--OUTPUT alignment_outputs/${sample_id}/${sample_id}.pe.50bp.bwa.sorted.mkdup.bam \
            	--METRICS_FILE alignment_outputs/${sample_id}/${sample_id}.markdups_metrics.txt \
            	--CREATE_INDEX true \
				--TMP_DIR \$TEMP
    	else
        	java -Xmx${task.memory.toGiga() - 1}g -XX:-UsePerfData -Djava.io.tmpdir="\$TEMP" -jar /usr/picard/picard.jar MarkDuplicates \
           		--INPUT ${bam} \
            	--OUTPUT alignment_outputs/${sample_id}/${sample_id}.pe.bwa.sorted.mkdup.bam \
            	--METRICS_FILE alignment_outputs/${sample_id}/${sample_id}.markdups_metrics.txt \
            	--CREATE_INDEX true \
				--TMP_DIR \$TEMP
    	fi
	else
		if [ ${params.crop_50} = true ]; then
            java -Xmx${task.memory.toGiga() - 1}g -XX:-UsePerfData -Djava.io.tmpdir="\$TEMP" -jar /usr/picard/picard.jar MarkDuplicates \
                --INPUT ${bam} \
                --OUTPUT alignment_outputs/${sample_id}/${sample_id}.se.50bp.bwa.sorted.mkdup.bam \
                --METRICS_FILE alignment_outputs/${sample_id}/${sample_id}markdups_metrics.txt \
                --CREATE_INDEX true \
				--TMP_DIR \$TEMP
        else
            java -Xmx${task.memory.toGiga() - 1}g -XX:-UsePerfData -Djava.io.tmpdir="\$TEMP" -jar /usr/picard/picard.jar MarkDuplicates \
                --INPUT ${bam} \
                --OUTPUT alignment_outputs/${sample_id}/${sample_id}.se.bwa.sorted.mkdup.bam \
                --METRICS_FILE alignment_outputs/${sample_id}/${sample_id}.markdups_metrics.txt \
                --CREATE_INDEX true \
				--TMP_DIR \$TEMP
        fi
	fi
 	"""
    stub:
    """
    test -f '${bam}'
    mkdir -p alignment_outputs/${sample_id}
    touch alignment_outputs/${sample_id}/${sample_id}.pe.bwa.sorted.mkdup.{bam,bai}
    touch alignment_outputs/${sample_id}/${sample_id}.markdups_metrics.txt
    """
}
