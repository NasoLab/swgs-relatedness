#!/usr/bin/env Rscript
# Tiny artificial assay objects exercise only shape/membership guards.
# No scientific result or numerical calling regression is generated.
suppressPackageStartupMessages({ library(QDNAseq); library(Biobase) })
args <- commandArgs(trailingOnly = TRUE)
checker <- normalizePath(args[[1]])
folder <- tempfile("public-cohort-contract-")
dir.create(folder)
expected <- file.path(folder, "expected.txt")
writeLines(c("sampleA", "sampleB"), expected)
bins <- data.frame(chromosome=c("1", "2", "X"), start=c(1, 1, 1),
                   end=c(500000, 500000, 500000), use=c(TRUE, TRUE, FALSE),
                   row.names=c("bin1", "bin2", "binX"))
cn <- matrix(1, nrow=3, ncol=2, dimnames=list(rownames(bins), c("sampleA", "sampleB")))
object <- new("QDNAseqCopyNumbers", bins=bins, copynumber=cn,
              phenodata=data.frame(name=colnames(cn), row.names=colnames(cn)))
assayDataElement(object, "segmented") <- cn
check <- function(value, should_pass) {
    path <- file.path(folder, "contract_copyNumbersSegmented.rds")
    saveRDS(value, path)
    result <- system2(file.path(R.home("bin"), "Rscript"),
                      vapply(c(checker, path, expected), shQuote, character(1)),
                      stdout=FALSE, stderr=FALSE)
    stopifnot(identical(result == 0L, should_pass))
}
check(object, TRUE)
check(object[, 1, drop=FALSE], FALSE) # missing sample
check(object[, 2:1], FALSE)          # wrong sample order
extra <- object
sampleNames(extra) <- c("sampleA", "sampleC")
check(extra, FALSE)                 # replacement/extra sample
sex <- object
fData(sex)$use[3] <- TRUE
check(sex, FALSE)                   # usable X bin
called <- object
assayDataElement(called, "calls") <- cn
check(called, FALSE)                # already-called source
narrow <- object
fData(narrow)$end <- c(50000, 50000, 50000)
check(narrow, FALSE)                # wrong bin size
unlink(folder, recursive=TRUE)
cat("PASS: seven cohort structure guards; no scientific computation\n")
