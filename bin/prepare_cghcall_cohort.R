#!/usr/bin/env Rscript

suppressPackageStartupMessages({
  library(Biobase)
  library(QDNAseq)
})

fixed_method <- "CGHcall"
fixed_organism <- "other"

usage <- function() {
  cat(
    paste(
      "Usage:",
      "  Rscript analyses/cohort_reporting/prepare_cghcall_cohort.R \\",
      "    --input-rds <500kb_noXY_copyNumbersSegmented.rds> \\",
      "    --output-rds <cohort_500kb_noXY_CGHcall.rds> \\",
      "    --expected-count <n> \\",
      "    --cohort <label> \\",
      "    [--expected-samples <csv|tsv|txt>] \\",
      "    [--sample-column sample_id] \\",
      "    [--compare-rds <historical_called.rds>] \\",
      "    [--comparison-tsv <comparison.tsv>] \\",
      "    [--provenance-txt <provenance.txt>] \\",
      "    [--overwrite]",
      "",
      "Scientific settings are fixed by provenance:",
      paste0("  method = ", fixed_method),
      paste0("  organism = ", fixed_organism),
      sep = "\n"
    )
  )
}

fail <- function(...) {
  stop(sprintf(...), call. = FALSE)
}

message_line <- function(...) {
  message(sprintf(...))
}

parse_args <- function(args) {
  out <- list(
    input_rds = NULL,
    output_rds = NULL,
    expected_count = NULL,
    expected_samples = NULL,
    sample_column = "sample_id",
    cohort = NULL,
    compare_rds = NULL,
    comparison_tsv = NULL,
    provenance_txt = NULL,
    overwrite = FALSE
  )

  i <- 1
  while (i <= length(args)) {
    key <- args[[i]]
    if (key %in% c("--help", "-h")) {
      usage()
      quit(save = "no", status = 0)
    }
    if (key == "--overwrite") {
      out$overwrite <- TRUE
      i <- i + 1
      next
    }
    if (!startsWith(key, "--")) {
      fail("Unexpected positional argument: %s", key)
    }
    if (i == length(args)) {
      fail("Missing value for argument %s", key)
    }
    value <- args[[i + 1]]
    name <- gsub("-", "_", sub("^--", "", key))
    if (!name %in% names(out)) {
      fail("Unknown argument: %s", key)
    }
    out[[name]] <- value
    i <- i + 2
  }

  required <- c("input_rds", "output_rds", "expected_count", "cohort")
  missing <- required[vapply(out[required], is.null, logical(1))]
  if (length(missing) > 0) {
    usage()
    fail("Missing required argument(s): %s", paste(paste0("--", gsub("_", "-", missing)), collapse = ", "))
  }

  out$expected_count <- suppressWarnings(as.integer(out$expected_count))
  if (is.na(out$expected_count) || out$expected_count <= 0) {
    fail("--expected-count must be a positive integer")
  }
  out
}

read_expected_samples <- function(path, sample_column) {
  if (!file.exists(path)) {
    fail("Expected sample file does not exist: %s", path)
  }

  ext <- tolower(tools::file_ext(path))
  if (ext == "txt") {
    values <- readLines(path, warn = FALSE)
    values <- trimws(values)
    values <- values[nzchar(values)]
    if (length(values) > 0 && values[[1]] == sample_column) {
      values <- values[-1]
    }
    return(values)
  }

  sep <- if (ext %in% c("tsv", "txt")) "\t" else ","
  df <- tryCatch(
    read.table(path, header = TRUE, sep = sep, stringsAsFactors = FALSE, check.names = FALSE, comment.char = ""),
    error = function(e) NULL
  )

  if (is.null(df) || ncol(df) == 0 || nrow(df) == 0) {
    values <- readLines(path, warn = FALSE)
    values <- trimws(values)
    values <- values[nzchar(values)]
    return(values)
  }

  if (sample_column %in% colnames(df)) {
    values <- df[[sample_column]]
  } else if (ncol(df) == 1) {
    message_line("Sample column '%s' not found; using the only column '%s'", sample_column, colnames(df)[[1]])
    values <- df[[1]]
  } else {
    fail("Expected sample file must contain column '%s'", sample_column)
  }

  trimws(as.character(values[nzchar(trimws(as.character(values)))]))
}

assay_matrix <- function(object, assay_name) {
  Biobase::assayDataElement(object, assay_name)
}

assay_names <- function(object) {
  Biobase::assayDataElementNames(object)
}

assert_unique <- function(values, label) {
  dup <- unique(values[duplicated(values)])
  if (length(dup) > 0) {
    fail("%s contains duplicate value(s): %s", label, paste(dup, collapse = ", "))
  }
}

validate_source_path <- function(path) {
  base <- basename(path)
  if (grepl("_bins_rCN\\.rds$", base) || grepl("_gl_rCN\\.rds$", base)) {
    fail(
      "Refusing called Step-1 object as Step-2A source: %s. Use the matching *_copyNumbersSegmented.rds object.",
      path
    )
  }
  if (!grepl("_copyNumbersSegmented\\.rds$", base)) {
    message_line("Input filename does not end in *_copyNumbersSegmented.rds: %s", base)
  }
}

validate_qdnaseq_source <- function(object, input_rds) {
  if (!inherits(object, "QDNAseqCopyNumbers")) {
    fail("Input object is not a QDNAseqCopyNumbers object: %s", paste(class(object), collapse = ", "))
  }

  names <- assay_names(object)
  required <- c("copynumber", "segmented")
  missing <- setdiff(required, names)
  if (length(missing) > 0) {
    fail("Input QDNAseq object is missing required assay(s): %s", paste(missing, collapse = ", "))
  }
  if ("calls" %in% names) {
    fail(
      "Input object already contains a calls assay and is not a supported Step-2A source: %s. Use *_copyNumbersSegmented.rds.",
      input_rds
    )
  }

  cn <- assay_matrix(object, "copynumber")
  seg <- assay_matrix(object, "segmented")
  if (!identical(dim(cn), dim(seg))) {
    fail("copynumber and segmented assays have different dimensions")
  }
  if (nrow(cn) <= 0 || ncol(cn) <= 0) {
    fail("Input assay dimensions are not sensible: %s", paste(dim(cn), collapse = "x"))
  }
  if (nrow(Biobase::fData(object)) != nrow(cn)) {
    fail("featureData row count does not match assay row count")
  }

  sample_ids <- colnames(cn)
  if (is.null(sample_ids) || any(!nzchar(sample_ids))) {
    fail("Input object has missing/blank sample IDs")
  }
  assert_unique(sample_ids, "Input sample IDs")

  invisible(sample_ids)
}

apply_expected_sample_list <- function(object, expected_samples) {
  current <- colnames(assay_matrix(object, "copynumber"))
  assert_unique(expected_samples, "Expected sample list")

  missing <- setdiff(expected_samples, current)
  extra <- setdiff(current, expected_samples)
  if (length(missing) > 0) {
    fail(
      "Expected sample list contains sample(s) missing from input: %s.",
      paste(missing, collapse = ", ")
    )
  }
  if (length(extra) > 0) {
    message_line("Expected sample list defines a subset cohort; excluding input sample(s): %s", paste(extra, collapse = ", "))
  }

  if (!identical(current, expected_samples)) {
    message_line("Input sample order/set differs from expected sample list; subsetting/reordering before CGHcall.")
    message_line("Input order: %s", paste(current, collapse = ", "))
    message_line("Expected order: %s", paste(expected_samples, collapse = ", "))
    object <- object[, expected_samples]
  }
  object
}

genomic_coordinate_columns <- function(object) {
  cols <- c("chromosome", "start", "end")
  intersect(cols, colnames(Biobase::fData(object)))
}

compare_numeric_matrix <- function(before, after, assay_name) {
  same_dim <- identical(dim(before), dim(after))
  same_dimnames <- identical(dimnames(before), dimnames(after))
  both_na <- is.na(before) & is.na(after)
  one_na <- xor(is.na(before), is.na(after))
  comparable <- !(is.na(before) | is.na(after))
  differing <- sum((before != after) & !both_na, na.rm = TRUE) + sum(one_na)
  max_abs <- if (any(comparable)) {
    max(abs(as.numeric(before[comparable]) - as.numeric(after[comparable])), na.rm = TRUE)
  } else {
    NA_real_
  }
  data.frame(
    assay = assay_name,
    same_dim = same_dim,
    same_dimnames = same_dimnames,
    differing_cells = differing,
    max_abs_diff = max_abs,
    stringsAsFactors = FALSE
  )
}

validate_called_output <- function(before, after) {
  before_samples <- colnames(assay_matrix(before, "copynumber"))
  after_samples <- colnames(assay_matrix(after, "copynumber"))
  if (!identical(before_samples, after_samples)) {
    fail("Sample IDs/order changed during callBins()")
  }
  if (!identical(dim(assay_matrix(before, "copynumber")), dim(assay_matrix(after, "copynumber")))) {
    fail("Assay dimensions changed during callBins()")
  }
  if (!identical(Biobase::fData(before), Biobase::fData(after))) {
    coord_cols <- genomic_coordinate_columns(before)
    if (length(coord_cols) == 0 || !identical(Biobase::fData(before)[, coord_cols, drop = FALSE], Biobase::fData(after)[, coord_cols, drop = FALSE])) {
      fail("featureData/genomic coordinates changed during callBins()")
    }
  }

  cn_compare <- compare_numeric_matrix(assay_matrix(before, "copynumber"), assay_matrix(after, "copynumber"), "copynumber")
  seg_compare <- compare_numeric_matrix(assay_matrix(before, "segmented"), assay_matrix(after, "segmented"), "segmented")
  if (cn_compare$differing_cells != 0 || seg_compare$differing_cells != 0) {
    fail("copynumber or segmented values changed during callBins()")
  }

  names <- assay_names(after)
  required <- c("calls", "probgain", "probloss", "probnorm")
  missing <- setdiff(required, names)
  if (length(missing) > 0) {
    fail("Called object is missing required CGHcall assay(s): %s", paste(missing, collapse = ", "))
  }
  optional <- c("probamp", "probdloss")
  missing_optional <- setdiff(optional, names)
  if (length(missing_optional) > 0) {
    message_line("Called object is missing optional high-level CGHcall assay(s): %s", paste(missing_optional, collapse = ", "))
  }

  calls <- assay_matrix(after, "calls")
  call_values <- sort(unique(as.vector(calls)))
  call_values <- call_values[!is.na(call_values)]
  if (!all(call_values %in% c(-2, -1, 0, 1, 2))) {
    fail("Unexpected call state value(s): %s", paste(call_values, collapse = ", "))
  }
  call_values
}

compare_to_reference <- function(new_object, reference_object) {
  new_assays <- assay_names(new_object)
  ref_assays <- assay_names(reference_object)
  all_assays <- union(new_assays, ref_assays)
  rows <- lapply(all_assays, function(assay) {
    if (!assay %in% new_assays || !assay %in% ref_assays) {
      return(data.frame(
        assay = assay,
        present_in_new = assay %in% new_assays,
        present_in_reference = assay %in% ref_assays,
        same_dim = NA,
        same_dimnames = NA,
        differing_cells = NA_integer_,
        max_abs_diff = NA_real_,
        stringsAsFactors = FALSE
      ))
    }
    cmp <- compare_numeric_matrix(assay_matrix(new_object, assay), assay_matrix(reference_object, assay), assay)
    cbind(
      data.frame(present_in_new = TRUE, present_in_reference = TRUE, stringsAsFactors = FALSE),
      cmp
    )[, c("assay", "present_in_new", "present_in_reference", "same_dim", "same_dimnames", "differing_cells", "max_abs_diff")]
  })
  do.call(rbind, rows)
}

write_provenance <- function(path, args, input_object, called_object, call_values, comparison_path = NULL) {
  lines <- c(
    paste("Cohort:", args$cohort),
    paste("Input segmented RDS:", normalizePath(args$input_rds, mustWork = TRUE)),
    paste("Output CGHcall RDS:", normalizePath(args$output_rds, mustWork = FALSE)),
    paste("Expected sample count:", args$expected_count),
    paste("Expected sample list:", if (is.null(args$expected_samples)) "<none>" else normalizePath(args$expected_samples, mustWork = TRUE)),
    paste("Fixed QDNAseq::callBins method:", fixed_method),
    paste("Fixed QDNAseq::callBins organism:", fixed_organism),
    paste("R version:", paste(R.version$major, R.version$minor, sep = ".")),
    paste("QDNAseq version:", as.character(utils::packageVersion("QDNAseq"))),
    paste("CGHcall version:", as.character(utils::packageVersion("CGHcall"))),
    paste("Biobase version:", as.character(utils::packageVersion("Biobase"))),
    paste("Sample count:", ncol(assay_matrix(called_object, "copynumber"))),
    paste("Bin count:", nrow(assay_matrix(called_object, "copynumber"))),
    paste("Input assays:", paste(assay_names(input_object), collapse = ", ")),
    paste("Output assays:", paste(assay_names(called_object), collapse = ", ")),
    paste("Observed call states:", paste(call_values, collapse = ", ")),
    paste("Comparison TSV:", if (is.null(comparison_path)) "<none>" else normalizePath(comparison_path, mustWork = FALSE)),
    "",
    "Important distinction:",
    "This Step-2A object is generated from the immutable Step-1 *_copyNumbersSegmented.rds using QDNAseq::callBins(method='CGHcall', organism='other').",
    "It is scientifically distinct from Nextflow's *_bins_rCN.rds object, which is produced by cutoff calling with cutoffs c(-0.1, 0.1).",
    "All samples intended for relatedness comparison must be present before CGHcall is run; adding samples later requires regenerating the cohort CGHcall object."
  )
  writeLines(lines, path)
}

args <- parse_args(commandArgs(trailingOnly = TRUE))

if (!file.exists(args$input_rds)) {
  fail("Input RDS does not exist: %s", args$input_rds)
}
if (file.exists(args$output_rds) && !isTRUE(args$overwrite)) {
  fail("Output RDS already exists: %s. Use --overwrite only for deliberate replacement.", args$output_rds)
}
if (!is.null(args$compare_rds) && !file.exists(args$compare_rds)) {
  fail("Comparison RDS does not exist: %s", args$compare_rds)
}

validate_source_path(args$input_rds)
dir.create(dirname(args$output_rds), recursive = TRUE, showWarnings = FALSE)

message_line("Step 2A cohort CGHcall preparation: %s", args$cohort)
message_line("Reading input segmented RDS: %s", args$input_rds)
qdnaseq <- readRDS(args$input_rds)
input_sample_ids <- validate_qdnaseq_source(qdnaseq, args$input_rds)

if (!is.null(args$expected_samples)) {
  expected_sample_ids <- read_expected_samples(args$expected_samples, args$sample_column)
  if (length(expected_sample_ids) != args$expected_count) {
    fail("Expected sample list has %d samples, expected %d", length(expected_sample_ids), args$expected_count)
  }
  qdnaseq <- apply_expected_sample_list(qdnaseq, expected_sample_ids)
} else {
  if (length(input_sample_ids) != args$expected_count) {
    fail("Input sample count is %d, expected %d", length(input_sample_ids), args$expected_count)
  }
  message_line("No expected sample list provided; preserving input sample order.")
}

call_sample_ids <- colnames(assay_matrix(qdnaseq, "copynumber"))
if (length(call_sample_ids) != args$expected_count) {
  fail("Prepared cohort sample count is %d, expected %d", length(call_sample_ids), args$expected_count)
}
message_line("Input samples: %s", paste(input_sample_ids, collapse = ", "))
message_line("Prepared cohort samples: %s", paste(call_sample_ids, collapse = ", "))
message_line("Running QDNAseq::callBins(organism = '%s', method = '%s') once across the complete cohort.", fixed_organism, fixed_method)
called <- QDNAseq::callBins(qdnaseq, organism = fixed_organism, method = fixed_method)
call_values <- validate_called_output(qdnaseq, called)

saveRDS(called, args$output_rds)
message_line("Wrote called cohort RDS: %s", args$output_rds)
message_line("Observed call states: %s", paste(call_values, collapse = ", "))

comparison_path <- args$comparison_tsv
if (!is.null(args$compare_rds)) {
  reference <- readRDS(args$compare_rds)
  comparison <- compare_to_reference(called, reference)
  if (is.null(comparison_path)) {
    comparison_path <- paste0(args$output_rds, ".comparison.tsv")
  }
  dir.create(dirname(comparison_path), recursive = TRUE, showWarnings = FALSE)
  write.table(comparison, comparison_path, sep = "\t", row.names = FALSE, quote = FALSE)
  message_line("Wrote comparison TSV: %s", comparison_path)
  print(comparison)
}

provenance_path <- args$provenance_txt
if (is.null(provenance_path)) {
  provenance_path <- paste0(args$output_rds, ".provenance.txt")
}
dir.create(dirname(provenance_path), recursive = TRUE, showWarnings = FALSE)
write_provenance(provenance_path, args, qdnaseq, called, call_values, comparison_path)
message_line("Wrote provenance: %s", provenance_path)
