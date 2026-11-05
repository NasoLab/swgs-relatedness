a <- commandArgs(TRUE)
dir.create(a[[1]], recursive=TRUE, showWarnings=FALSE)
fields <- c("Package", "Version", "Built", "License", "Depends", "Imports", "LinkingTo", "SystemRequirements", "Repository", "RemoteType", "RemoteHost", "RemoteUsername", "RemoteRepo", "RemoteRef", "RemoteSha", "GithubSHA1", "URL")
rows <- lapply(sort(rownames(installed.packages())), function(pkg) {
    path <- system.file("DESCRIPTION", package=pkg)
    d <- read.dcf(path)
    v <- vapply(fields, function(f) if (f %in% colnames(d)) d[1,f] else "", character(1))
    v <- gsub("[\r\n\t]+", " ", v)
    c(v, LibraryScope=if (startsWith(normalizePath(dirname(path)), normalizePath(R.home()))) "runtime" else "external")
})
x <- as.data.frame(do.call(rbind, rows), stringsAsFactors=FALSE)
write.table(x, file.path(a[[1]], "r-packages.tsv"), sep="\t", row.names=FALSE, quote=FALSE, na="")
base <- c(paste("R:", getRversion()), paste("Platform:", R.version$platform),
          paste("Bioconductor recorded:", if (requireNamespace("BiocVersion",quietly=TRUE)) as.character(packageVersion("BiocVersion")) else "unknown (BiocVersion absent)"),
          paste("RNGkind:", paste(RNGkind(),collapse=" / ")),
          paste(names(extSoftVersion()), ifelse(startsWith(extSoftVersion(), "/"), basename(extSoftVersion()), extSoftVersion()), sep=": "))
writeLines(base, file.path(a[[1]], "runtime.txt"))
