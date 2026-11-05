process TRIMMOMATIC {
    tag "trimming reads of $sample_id"

	container 'docker://staphb/trimmomatic:latest'    
	cpus 8
	memory '32 GB'
	scratch '/tmp'
	// time '10h'

    input:
    tuple val(sample_id), path(reads, stageAs: 'reads/read??/*')

    output:
	tuple val(sample_id), path("trimmed/${sample_id}/*")

    script:
    def read_list = reads instanceof List ? reads : [reads]
    def read_args = read_list.collect { "'" + it.toString().replace("'", "'\"'\"'") + "'" }.join(' ')
	"""
	set -euo pipefail

	TMP_DIR=\$(mktemp -d "\${TMPDIR:-/tmp}/${sample_id}.trim.XXXXXX")
	trap 'rm -rf "\$TMP_DIR"' EXIT
	mkdir -p "trimmed/${sample_id}"

	if [ ${params.crop_50} = true ]; then  
		if [ ${params.paired_end} = true ]; then 
			trimmomatic PE -threads ${task.cpus} -phred33 ${read_args} \
                "\$TMP_DIR/${sample_id}.f.paired.fastq.gz" \
                "\$TMP_DIR/${sample_id}.f.unpaired.fastq.gz" \
                "\$TMP_DIR/${sample_id}.r.paired.fastq.gz" \
                "\$TMP_DIR/${sample_id}.r.unpaired.fastq.gz" \
                ILLUMINACLIP:/usr/local/bin/adapters/TruSeq3-PE-2.fa:2:30:10:2:true \
                LEADING:3 TRAILING:3 SLIDINGWINDOW:4:15 MINLEN:36 MAXINFO:100:0.5 CROP:50
		else
            trimmomatic SE -threads ${task.cpus} -phred33 ${read_args} \
                "\$TMP_DIR/${sample_id}.se.fastq.gz" \
                ILLUMINACLIP:/usr/local/bin/adapters/TruSeq3-SE.fa:2:30:10:2 \
                LEADING:3 TRAILING:3 SLIDINGWINDOW:4:15 MINLEN:36 MAXINFO:100:0.5 CROP:50
		fi
	else
		if [ ${params.paired_end} = true ]; then
            trimmomatic PE -threads ${task.cpus} -phred33 ${read_args} \
                "\$TMP_DIR/${sample_id}.f.paired.fastq.gz" \
                "\$TMP_DIR/${sample_id}.f.unpaired.fastq.gz" \
                "\$TMP_DIR/${sample_id}.r.paired.fastq.gz" \
                "\$TMP_DIR/${sample_id}.r.unpaired.fastq.gz" \
                ILLUMINACLIP:/usr/local/bin/adapters/TruSeq3-PE-2.fa:2:30:10:2:true \
                LEADING:3 TRAILING:3 SLIDINGWINDOW:4:15 MINLEN:36 MAXINFO:100:0.5
		else
            trimmomatic SE -threads ${task.cpus} -phred33 ${read_args} \
                "\$TMP_DIR/${sample_id}.se.fastq.gz" \
                ILLUMINACLIP:/usr/local/bin/adapters/TruSeq3-SE.fa:2:30:10:2 \
                LEADING:3 TRAILING:3 SLIDINGWINDOW:4:15 MINLEN:36 MAXINFO:100:0.5
		fi
	fi

	mv "\$TMP_DIR"/* "trimmed/${sample_id}/"
	"""
    stub:
    def read_list = reads instanceof List ? reads : [reads]
    def read_args = read_list.collect { "'" + it.toString().replace("'", "'\"'\"'") + "'" }.join(' ')
    def output_names = params.paired_end ? "${sample_id}.{f,r}.{paired,unpaired}.fastq.gz" : "${sample_id}.se.fastq.gz"
    """
    for read in ${read_args}; do test -f "\$read"; done
    mkdir -p trimmed/${sample_id}
    touch trimmed/${sample_id}/${output_names}
    """
}
