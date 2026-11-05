# UNBUILT source-restoration assembly; both input runtimes require rights/source review.
# No source archives, images or scientific references are distributed with this recipe.
ARG LLR_IMAGE
ARG GENERAL_IMAGE
FROM ${LLR_IMAGE} AS llr
FROM ${GENERAL_IMAGE}
ARG LLR_IMAGE
ARG GENERAL_IMAGE
RUN for image in "$LLR_IMAGE" "$GENERAL_IMAGE"; do case "$image" in *@sha256:*) ;; *) exit 2;; esac; done
COPY --from=llr /opt/swgs/llr-r /opt/swgs/llr-r
RUN mkdir -p /opt/swgs/bin && ln -s /opt/swgs/llr-r/bin/Rscript /opt/swgs/bin/Rscript-llr
ENV PATH="/opt/swgs/bin:/opt/swgs/general-r/bin:${PATH}"
LABEL org.opencontainers.image.description="Unvalidated combined SWGS runtime; separate R prefixes; all regression gates required"
