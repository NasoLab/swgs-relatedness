#!/usr/bin/env Rscript
# Reuse established function bodies without invoking their standalone CLI driver.
suppressPackageStartupMessages({ library(QDNAseq); library(Biobase) })
a <- commandArgs(trailingOnly=TRUE)
stopifnot(length(a) %in% c(7L, 8L))
mode <- if (length(a) == 8L) a[[8]] else "all"
stopifnot(mode %in% c("all", "pcc_regression"))
a <- a[1:7]
names(a) <- c("called", "samples", "pairs", "runner", "pfreq", "helper", "out")
dir.create(a[["out"]], recursive=TRUE, showWarnings=FALSE)
write_precise <- function(x, name) {
    x[] <- lapply(x, function(v) if (is.double(v)) ifelse(is.na(v), NA_character_, sprintf("%.17g", v)) else v)
    write.table(x, file.path(a[["out"]], name), sep="\t", quote=FALSE, row.names=FALSE, na="NA")
}
# Evaluate the unmodified imports/definitions only, stopping at the CLI main.
env <- new.env(parent=globalenv())
expressions <- as.list(parse(a[["runner"]]))
main <- which(vapply(expressions, function(e) is.call(e) && identical(e[[1]], as.name("<-")) &&
    identical(e[[2]], as.name("args")), logical(1)))
stopifnot(length(main) == 1L, main > 1L)
for (e in expressions[seq_len(main - 1L)]) eval(e, env)
expected <- readLines(a[["samples"]], warn=FALSE)
object <- readRDS(a[["called"]])
stopifnot(inherits(object, "QDNAseqCopyNumbers"), !anyDuplicated(expected),
          length(expected) > 0L, identical(sampleNames(object), expected))
used <- QDNAseq:::binsToUse(object)
stopifnot(any(used), !any(as.character(fData(object)$chromosome[used]) %in% c("X", "Y", "23", "24")),
          all(c("copynumber", "segmented", "calls") %in% assayDataElementNames(object)))
cn <- assayDataElement(object, "copynumber")
seg <- assayDataElement(object, "segmented")
stopifnot(identical(dim(cn), dim(seg)), identical(colnames(cn), expected))
qc <- data.frame(sample_id=expected, usable_bins=sum(used),
    finite_segmented_bins=colSums(is.finite(seg[used, , drop=FALSE])),
    call_states=vapply(expected, function(s) paste(sort(unique(assayDataElement(object, "calls")[used,s])), collapse=","), character(1)),
    stringsAsFactors=FALSE)
write_precise(qc, "sample_qc.tsv")
pairs <- read.csv(a[["pairs"]], stringsAsFactors=FALSE, check.names=FALSE)
if (nrow(pairs)) {
    info <- env$validate_called_rds(a[["called"]])
    pairs <- env$read_pair_metadata(a[["pairs"]], info$sample_ids, nrow(pairs))
    context_args <- list(pfreq=a[["pfreq"]], clonality_functions=a[["helper"]])
    # Same execution order as the original driver, including seed placement.
    segment_long <- env$make_segment_long(object)
    pcc <- env$compute_pcc(pairs, segment_long)
    if (mode == "all") {
        availability <- env$llr_availability(context_args)
        if (!availability$ok) stop(paste("LLR environment unavailable:", availability$status))
        context <- env$prepare_llr(context_args)
        set.seed(1337)
        llr <- env$compute_llr(pairs, object, context$ref_data)
    } else {
        llr <- data.frame(llr=rep(NA_real_, nrow(pairs)), llr_status="not_requested_regression_only")
    }
    values <- data.frame(pair_id=pairs$pair_id, sample1=pairs$sample1, sample2=pairs$sample2,
                         pcc=pcc, llr=llr$llr, llr_status=llr$llr_status, stringsAsFactors=FALSE)
} else {
    values <- data.frame(pair_id=character(), sample1=character(), sample2=character(),
                         pcc=numeric(), llr=numeric(), llr_status=character())
}
write_precise(values, "pcc_llr.tsv")
writeLines(c(paste("RNGkind:", paste(RNGkind(), collapse=" / ")),
             "LLR seed: 1337 once after helper/PFREQ loading; ordered sequential loop",
             capture.output(sessionInfo())), file.path(a[["out"]], "pcc_llr_environment.txt"))
