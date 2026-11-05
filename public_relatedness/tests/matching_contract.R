#!/usr/bin/env Rscript
# Synthetic geometry checks of supplied recovered code; not scientific fixtures.
suppressPackageStartupMessages({ library(data.table); library(GenomicRanges) })
a <- commandArgs(TRUE)
helper <- new.env(parent=globalenv())
for (e in as.list(parse(a[[1]]))) {
    if (is.call(e) && identical(e[[1]], as.name("<-")) && identical(e[[2]], as.name("getHit"))) eval(e, helper)
}
segments <- data.table(SampleID=c("A", "B"), Chr=c("1", "1"), SVType=c("DEL", "DEL"),
                       Start=c(1, 2500001), End=c(5000000, 7500000))
count <- function(x) {
    h <- helper$getHit(x, c("A", "B"), "VCF", 2500000)
    sum(vapply(h[[1]], length, integer(1))) + sum(vapply(h[[2]], length, integer(1)))
}
stopifnot(count(segments) == 2L)
x <- copy(segments); x[SampleID == "B", `:=`(Start=2500002, End=7500001)]
stopifnot(count(x) == 0L)
x <- copy(segments); x[SampleID == "B", SVType := "DUP"]
stopifnot(count(x) == 0L)
x <- copy(segments); x[SampleID == "B", Chr := "2"]
stopifnot(count(x) == 0L)
x <- copy(segments); x[SampleID == "B", `:=`(Start=5000000, End=15000000)]
stopifnot(count(x) == 0L)
x <- rbind(segments, data.table(SampleID="A", Chr="1", SVType="DEL", Start=2000000, End=6000000))
stopifnot(count(x) == 4L) # multiple hits retained, despite negative historical private count
cat("PASS: six recovered-matching geometry checks\n")
