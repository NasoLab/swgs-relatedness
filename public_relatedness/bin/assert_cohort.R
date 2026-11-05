#!/usr/bin/env Rscript
# Reject extra profiles before the inherited caller can subset a cohort.
suppressPackageStartupMessages({ library(QDNAseq); library(Biobase) })
args <- commandArgs(trailingOnly = TRUE)
stopifnot(length(args) == 2L)
object <- readRDS(args[[1]])
expected <- readLines(args[[2]], warn = FALSE)
stopifnot(inherits(object, "QDNAseqCopyNumbers"), length(expected) > 0L,
          !anyDuplicated(expected), identical(sampleNames(object), expected),
          all(c("copynumber", "segmented") %in% assayDataElementNames(object)),
          !"calls" %in% assayDataElementNames(object))
used <- QDNAseq:::binsToUse(object)
stopifnot(any(used), !any(as.character(fData(object)$chromosome[used]) %in% c("X", "Y", "23", "24")))
widths <- fData(object)$end - fData(object)$start + 1
stopifnot(as.numeric(names(sort(table(widths[used]), decreasing = TRUE))[1]) == 500000)
