#!/usr/bin/env Rscript
# Evaluate only the recovered expressions/functions supplied by the operator.
suppressPackageStartupMessages({
    library(QDNAseq); library(Biobase); library(utanos)
    library(dplyr); library(tidyr); library(data.table); library(GenomicRanges)
})
a <- commandArgs(trailingOnly=TRUE)
stopifnot(length(a) == 6L)
names(a) <- c("called", "samples", "pairs", "preprocessing", "matching", "out")
dir.create(a[["out"]], recursive=TRUE, showWarnings=FALSE)
load_assignments <- function(path, names, env) {
    expressions <- as.list(parse(path))
    for (name in names) {
        found <- Filter(function(e) is.call(e) && identical(e[[1]], as.name("<-")) &&
                        identical(e[[2]], as.name(name)), expressions)
        stopifnot(length(found) == 1L)
        eval(found[[1]], env)
    }
}
env <- new.env(parent=globalenv())
env$rcn_cohort <- readRDS(a[["called"]])
expected <- readLines(a[["samples"]], warn=FALSE)
stopifnot(identical(sampleNames(env$rcn_cohort), expected), !anyDuplicated(expected))
# This is the sole replacement of historical QC/population membership selection.
env$combined_metadata_usable <- data.frame(sample_id=expected)
load_assignments(a[["preprocessing"]],
    c("rcn_cohort_segs", "rcn_cohort_calls", "rcn_cohort_collapse", "df_cohort"), env)
segments <- as.data.table(env$df_cohort)
stopifnot(all(segments$SampleID %in% expected), all(segments$SVType %in% c("DUP", "DEL")))
class(segments$End) <- "character"
class(segments$Length) <- "integer"
helper <- new.env(parent=globalenv())
load_assignments(a[["matching"]], c("getHit", "calculateMaxGap"), helper)
if (nrow(segments)) stopifnot(helper$calculateMaxGap(segments, "VCF") == 2500000)
observations <- bind_rows(
    as.data.frame(segments) %>% transmute(SampleID, Chr=as.character(Chr), SVType,
                                         boundary_type="start", coordinate=as.numeric(Start)),
    as.data.frame(segments) %>% transmute(SampleID, Chr=as.character(Chr), SVType,
                                         boundary_type="end", coordinate=as.numeric(End)))
pairs <- read.csv(a[["pairs"]], stringsAsFactors=FALSE, check.names=FALSE)
counts <- lapply(seq_len(nrow(pairs)), function(i) {
    pair <- c(pairs$sample1[[i]], pairs$sample2[[i]])
    nA <- 2L * sum(segments$SampleID == pair[[1]])
    nB <- 2L * sum(segments$SampleID == pair[[2]])
    H <- 0L
    if (nA > 0L && nB > 0L) {
        hits <- helper$getHit(segments, pair, "VCF", 2500000)
        H <- sum(vapply(hits[[1]], length, integer(1))) + sum(vapply(hits[[2]], length, integer(1)))
    }
    data.frame(pair_id=pairs$pair_id[[i]], sample1=pair[[1]], sample2=pair[[2]],
               shared=H, private_sample1=nA-H, private_sample2=nB-H, total=nA+nB-H)
})
write.table(observations, file.path(a[["out"]], "observations.tsv"), sep="\t", quote=FALSE, row.names=FALSE)
write.table(bind_rows(counts), file.path(a[["out"]], "breakpoint_counts.tsv"), sep="\t", quote=FALSE, row.names=FALSE)
writeLines(c(paste("utanos RemoteSha:", packageDescription("utanos")$RemoteSha),
             "Matching tolerance: 2500000 inclusive; recovered getHit all overlaps",
             capture.output(sessionInfo())), file.path(a[["out"]], "breakpoint_environment.txt"))
