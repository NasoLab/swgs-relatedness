# DRAFT, UNBUILT, NOT VALIDATED. No third-party sources are provided.
# Build context must contain reviewed approved-sources/ outside public Git.
ARG BASE_IMAGE
FROM ${BASE_IMAGE}
ARG BASE_IMAGE
USER root
RUN case "$BASE_IMAGE" in *@sha256:*) ;; *) exit 2;; esac
COPY general-r/conda-explicit-linux-64.txt /opt/spec/conda.txt
RUN micromamba create -y -p /opt/swgs/general-r -f /opt/spec/conda.txt
COPY general-r/ /opt/spec/runtime/
COPY restore_r.R verify_r.R /opt/spec/
COPY approved-sources/ /opt/approved-sources/
RUN /opt/swgs/general-r/bin/Rscript /opt/spec/restore_r.R /opt/spec/runtime/r-packages.tsv /opt/approved-sources/manifest.tsv /opt/approved-sources
RUN /opt/swgs/general-r/bin/Rscript /opt/spec/verify_r.R /opt/spec/runtime/r-packages.tsv /opt/spec/runtime/runtime.txt
ENV PATH="/opt/swgs/general-r/bin:${PATH}"
LABEL org.opencontainers.image.description="Unvalidated SWGS general-r restoration candidate; regressions required"

RUN mkdir -p /opt/swgs/bin && ln -s /opt/swgs/general-r/bin/Rscript /opt/swgs/bin/Rscript-general
ENV PATH="/opt/swgs/bin:${PATH}"
