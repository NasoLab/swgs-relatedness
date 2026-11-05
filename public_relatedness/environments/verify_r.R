#!/usr/bin/env Rscript
# Metadata gate only: matching versions do not prove numerical equivalence.
a <- commandArgs(TRUE)
stopifnot(length(a) == 2L)
expected <- read.delim(a[[1]], check.names=FALSE, stringsAsFactors=FALSE, colClasses="character", na.strings=NULL)
runtime <- readLines(a[[2]])
expected_r <- sub("^R: ", "", runtime[startsWith(runtime, "R: ")])
stopifnot(length(expected_r) == 1L, identical(as.character(getRversion()), expected_r))
installed <- installed.packages()
missing <- setdiff(expected$Package, rownames(installed))
if (length(missing)) stop(paste("Missing packages:", paste(missing, collapse=", ")))
wrong <- expected$Package[installed[expected$Package, "Version"] != expected$Version]
if (length(wrong)) stop(paste("Package version mismatch:", paste(wrong, collapse=", ")))
cat("Metadata matches", nrow(expected), "recorded package versions; numerical/container validation still required.\n")
