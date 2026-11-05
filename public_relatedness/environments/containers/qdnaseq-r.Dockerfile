# DRAFT wrapper of an independently recovered permission-cleared OCI image.
# The original OCI manifest digest is unknown; a SIF SHA256 is NOT an OCI digest.
ARG QDNASEQ_IMAGE
FROM ${QDNASEQ_IMAGE}
ARG QDNASEQ_IMAGE
RUN case "$QDNASEQ_IMAGE" in *@sha256:*) ;; *) exit 2;; esac
COPY qdnaseq-r/ /opt/spec/qdnaseq-r/
COPY verify_r.R /opt/spec/verify_r.R
RUN Rscript /opt/spec/verify_r.R /opt/spec/qdnaseq-r/r-packages.tsv /opt/spec/qdnaseq-r/runtime.txt
LABEL org.opencontainers.image.description="Unbuilt QDNAseq preservation candidate; numerical validation pending"
