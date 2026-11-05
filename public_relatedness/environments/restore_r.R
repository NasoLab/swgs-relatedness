#!/usr/bin/env Rscript
# Draft offline restoration into a NEW environment only; never called by pipeline.
a <- commandArgs(TRUE)
stopifnot(length(a) == 3L)
expected <- read.delim(a[[1]], check.names=FALSE, stringsAsFactors=FALSE, colClasses="character", na.strings=NULL)
manifest <- read.delim(a[[2]], stringsAsFactors=FALSE, check.names=FALSE, colClasses="character", na.strings=NULL)
stopifnot(all(c("Package", "Version", "Filename", "SHA256", "permission_reference") %in% names(manifest)),
          !anyDuplicated(manifest$Package))
source_dir <- normalizePath(a[[3]], mustWork=TRUE)
installed <- installed.packages()
needs <- expected$Package[vapply(expected$Package, function(p) {
    !p %in% rownames(installed) || installed[p,"Version"] != expected$Version[expected$Package == p]
}, logical(1))]
# Git/manual packages must be restored from reviewed archives even if version matches.
manual <- expected$Package[expected$RemoteSha != "" | expected$Package == "QDNAseq.dev"]
needs <- union(needs, manual)
if (length(setdiff(needs, manifest$Package))) stop("Source archive manifest is incomplete; do not install current repository versions")
for (pkg in needs) {
    row <- manifest[manifest$Package == pkg, , drop=FALSE]
    stopifnot(row$Version == expected$Version[expected$Package == pkg],
              nzchar(row$permission_reference), grepl("^[a-f0-9]{64}$", row$SHA256),
              basename(row$Filename) == row$Filename)
    path <- normalizePath(file.path(source_dir, row$Filename), mustWork=TRUE)
    stopifnot(startsWith(path, paste0(source_dir, "/")))
    digest <- strsplit(system2("sha256sum", shQuote(path), stdout=TRUE), " ")[[1]][1]
    if (digest != row$SHA256) stop(paste("Archive checksum mismatch:", pkg))
}
# Dependency ordering uses the recorded dependency names; no network or solver.
dependencies <- function(pkg) {
    row <- expected[expected$Package == pkg, , drop=FALSE]
    text <- paste(row$Depends, row$Imports, row$LinkingTo, sep=",")
    values <- trimws(gsub("\\s*\\([^)]*\\)", "", strsplit(text, ",")[[1]]))
    intersect(values[nzchar(values)], expected$Package)
}
while (length(needs)) {
    ready <- needs[vapply(needs, function(p) !any(dependencies(p) %in% needs), logical(1))]
    if (!length(ready)) stop("Unresolved dependency cycle; recover the original build order")
    for (pkg in ready) {
        row <- manifest[manifest$Package == pkg, , drop=FALSE]
        install.packages(file.path(source_dir, row$Filename), repos=NULL, type="source")
        if (as.character(packageVersion(pkg)) != row$Version) stop(paste("Restored package version mismatch:", pkg))
    }
    needs <- setdiff(needs, ready)
}
