#!/usr/bin/env Rscript

suppressPackageStartupMessages({
  library(Biobase)
  library(DNAcopy)
  library(dplyr)
  library(QDNAseq)
  library(tidyr)
})

pcc_related_threshold <- 0.54
pcc_inconclusive_threshold <- 0.45
llr_related_threshold <- 0
llr_inconclusive_threshold <- -5

usage <- function() {
  cat(
    paste(
      "Usage:",
      "  Rscript analyses/cohort_reporting/run_pcc_llr.R \\",
      "    --called-rds <step2a_cghcall.rds> \\",
      "    --pairs <pair_metadata.csv> \\",
      "    --output-dir <step2c_output_dir> \\",
      "    --cohort <label> \\",
      "    --expected-pairs <n> \\",
      "    [--pfreq <pfreq_lusc_tcga_split.csv>] \\",
      "    [--clonality-functions <clonality_analysis_PFREQ_MOD.R>] \\",
      "    [--compare-pcc-csv <historical_pcc_table.csv>]",
      "",
      "PCC settings fixed from historical do_pcc_lrr_method.R:",
      "  PCC is Pearson correlation across log2 segmented 500 kb no-XY bins",
      paste0("  pcc > ", pcc_related_threshold, " -> related"),
      paste0("  pcc >= ", pcc_inconclusive_threshold, " -> inconclusive"),
      "  otherwise -> unrelated",
      "",
      "LLR is optional. It is attempted only when pfreq/helper paths are supplied",
      "and QDNAseq.dev plus Clonality are installed in the active R environment.",
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
    called_rds = NULL,
    pairs = NULL,
    output_dir = NULL,
    cohort = NULL,
    expected_pairs = NULL,
    pfreq = NULL,
    clonality_functions = NULL,
    compare_pcc_csv = NULL
  )

  i <- 1
  while (i <= length(args)) {
    key <- args[[i]]
    if (key %in% c("--help", "-h")) {
      usage()
      quit(save = "no", status = 0)
    }
    if (!startsWith(key, "--")) {
      fail("Unexpected positional argument: %s", key)
    }
    if (i == length(args)) {
      fail("Missing value for argument %s", key)
    }
    name <- gsub("-", "_", sub("^--", "", key))
    if (!name %in% names(out)) {
      fail("Unknown argument: %s", key)
    }
    out[[name]] <- args[[i + 1]]
    i <- i + 2
  }

  required <- c("called_rds", "pairs", "output_dir", "cohort", "expected_pairs")
  missing <- required[vapply(out[required], is.null, logical(1))]
  if (length(missing) > 0) {
    usage()
    fail("Missing required argument(s): %s", paste(paste0("--", gsub("_", "-", missing)), collapse = ", "))
  }

  out$expected_pairs <- suppressWarnings(as.integer(out$expected_pairs))
  if (is.na(out$expected_pairs) || out$expected_pairs < 1) {
    fail("--expected-pairs must be a positive integer")
  }
  out
}

assay_names <- function(object) {
  Biobase::assayDataElementNames(object)
}

assay_matrix <- function(object, assay_name) {
  Biobase::assayDataElement(object, assay_name)
}

validate_called_rds <- function(path) {
  if (!file.exists(path)) {
    fail("Called RDS does not exist: %s", path)
  }
  base <- basename(path)
  if (grepl("_copyNumbersSegmented\\.rds$", base) || grepl("_bins_rCN\\.rds$", base) || grepl("_gl_rCN\\.rds$", base)) {
    fail("Refusing non-Step-2A called object as Step-2C input: %s. Use the Step-2A CGHcall cohort RDS.", path)
  }

  object <- readRDS(path)
  if (!inherits(object, "QDNAseqCopyNumbers")) {
    fail("Called RDS is not a QDNAseqCopyNumbers object: %s", paste(class(object), collapse = ", "))
  }

  required <- c("copynumber", "segmented", "calls", "probamp", "probdloss", "probgain", "probloss", "probnorm")
  missing <- setdiff(required, assay_names(object))
  if (length(missing) > 0) {
    fail("Called RDS is missing Step-2A CGHcall assay(s): %s", paste(missing, collapse = ", "))
  }

  cn <- assay_matrix(object, "copynumber")
  seg <- assay_matrix(object, "segmented")
  calls <- assay_matrix(object, "calls")
  if (!identical(dim(cn), dim(seg)) || !identical(dim(cn), dim(calls))) {
    fail("copynumber, segmented, and calls assays do not have matching dimensions")
  }
  if (nrow(cn) <= 0 || ncol(cn) <= 1) {
    fail("Called RDS dimensions are not sensible: %s", paste(dim(cn), collapse = "x"))
  }

  sample_ids <- colnames(cn)
  if (is.null(sample_ids) || any(!nzchar(sample_ids))) {
    fail("Called RDS has missing/blank sample IDs")
  }
  if (any(duplicated(sample_ids))) {
    fail("Called RDS contains duplicate sample IDs: %s", paste(unique(sample_ids[duplicated(sample_ids)]), collapse = ", "))
  }

  call_values <- sort(unique(as.vector(calls)))
  call_values <- call_values[!is.na(call_values)]
  if (!all(call_values %in% c(-2, -1, 0, 1, 2))) {
    fail("Unexpected call state value(s): %s", paste(call_values, collapse = ", "))
  }
  if (!any(call_values %in% c(-2, 2))) {
    fail("Called RDS does not show high-level CGHcall states -2/2; it may be a cutoff-called object")
  }

  list(object = object, sample_ids = sample_ids, call_values = call_values)
}

pair_key <- function(sample1, sample2) {
  paste(pmin(sample1, sample2), pmax(sample1, sample2), sep = "___")
}

read_pair_metadata <- function(path, sample_ids, expected_pairs) {
  if (!file.exists(path)) {
    fail("Pair metadata does not exist: %s", path)
  }
  pairs <- read.csv(path, stringsAsFactors = FALSE, check.names = FALSE, na.strings = c("", "NA"))

  if (all(c("Sample1", "Sample2") %in% colnames(pairs)) && !all(c("sample1", "sample2") %in% colnames(pairs))) {
    pairs <- pairs %>% rename(sample1 = Sample1, sample2 = Sample2)
  }
  required <- c("sample1", "sample2")
  missing <- setdiff(required, colnames(pairs))
  if (length(missing) > 0) {
    fail("Pair metadata is missing required column(s): %s", paste(missing, collapse = ", "))
  }

  pairs <- pairs %>%
    mutate(
      sample1 = trimws(as.character(sample1)),
      sample2 = trimws(as.character(sample2))
    ) %>%
    filter(!is.na(sample1), !is.na(sample2), sample1 != "", sample2 != "")

  if (nrow(pairs) != expected_pairs) {
    fail("Pair metadata has %d usable pair(s), expected %d", nrow(pairs), expected_pairs)
  }
  if (any(pairs$sample1 == pairs$sample2)) {
    fail("Pair metadata contains self-pair(s)")
  }

  missing_samples <- sort(unique(c(setdiff(pairs$sample1, sample_ids), setdiff(pairs$sample2, sample_ids))))
  if (length(missing_samples) > 0) {
    fail("Pair metadata references sample(s) absent from called RDS: %s", paste(missing_samples, collapse = ", "))
  }

  pairs$pair_key <- pair_key(pairs$sample1, pairs$sample2)
  if (any(duplicated(pairs$pair_key))) {
    fail("Pair metadata contains duplicate unordered pair(s): %s", paste(unique(pairs$pair_key[duplicated(pairs$pair_key)]), collapse = ", "))
  }

  pairs
}

export_bins_qdnaseq_obj <- function(object, type = c("copynumber", "segments", "calls"), filter = TRUE, digits = 3) {
  type <- match.arg(type)
  if (!inherits(object, "QDNAseqSignals")) {
    fail("Only QDNAseqSignals-derived objects are supported")
  }
  if (filter) {
    object <- object[QDNAseq:::binsToUse(object), ]
  }

  dat <- switch(
    type,
    copynumber = assay_matrix(object, "copynumber"),
    segments = assay_matrix(object, "segmented"),
    calls = assay_matrix(object, "calls")
  )
  if (is.numeric(digits)) {
    dat <- round(dat, digits = digits)
  }

  data.frame(
    feature = Biobase::featureNames(object),
    chromosome = Biobase::fData(object)$chromosome,
    start = Biobase::fData(object)$start,
    end = Biobase::fData(object)$end,
    dat,
    check.names = FALSE,
    stringsAsFactors = FALSE
  )
}

make_segment_long <- function(qdnaseq_obj) {
  export_bins_qdnaseq_obj(object = qdnaseq_obj, type = "segments") %>%
    pivot_longer(
      cols = !any_of(c("feature", "chromosome", "start", "end")),
      names_to = "sample_id",
      values_to = "segmented"
    ) %>%
    arrange(sample_id) %>%
    select(-feature) %>%
    relocate(sample_id) %>%
    mutate(segmented = log2(segmented))
}

classify_pcc <- function(pcc) {
  case_when(
    pcc > pcc_related_threshold ~ "related",
    pcc >= pcc_inconclusive_threshold ~ "inconclusive",
    TRUE ~ "unrelated"
  )
}

classify_llr <- function(llr) {
  case_when(
    is.na(llr) ~ NA_character_,
    llr > llr_related_threshold ~ "related",
    llr >= llr_inconclusive_threshold ~ "inconclusive",
    TRUE ~ "unrelated"
  )
}

classify_combined <- function(pcc, llr) {
  case_when(
    is.na(llr) ~ NA_character_,
    pcc > pcc_related_threshold & llr > llr_related_threshold ~ "related",
    pcc >= pcc_inconclusive_threshold & llr >= llr_inconclusive_threshold ~ "inconclusive",
    TRUE ~ "unrelated"
  )
}

compute_pcc <- function(pairs, segment_long) {
  vapply(seq_len(nrow(pairs)), function(i) {
    sample_one <- pairs$sample1[[i]]
    sample_two <- pairs$sample2[[i]]
    sample_one_df <- segment_long %>% filter(sample_id == sample_one)
    sample_two_df <- segment_long %>% filter(sample_id == sample_two)
    stats::cor(sample_one_df$segmented, sample_two_df$segmented, method = "pearson")
  }, numeric(1))
}

llr_availability <- function(args) {
  if (is.null(args$pfreq) || is.null(args$clonality_functions)) {
    return(list(ok = FALSE, status = "skipped_no_llr_inputs"))
  }
  if (!file.exists(args$pfreq)) {
    return(list(ok = FALSE, status = "skipped_missing_pfreq"))
  }
  if (!file.exists(args$clonality_functions)) {
    return(list(ok = FALSE, status = "skipped_missing_clonality_functions"))
  }
  if (!requireNamespace("QDNAseq.dev", quietly = TRUE)) {
    return(list(ok = FALSE, status = "skipped_missing_QDNAseq.dev"))
  }
  if (!requireNamespace("Clonality", quietly = TRUE)) {
    return(list(ok = FALSE, status = "skipped_missing_Clonality"))
  }
  list(ok = TRUE, status = "computed")
}

prepare_llr <- function(args) {
  suppressPackageStartupMessages({
    library(Clonality)
    library(QDNAseq.dev)
  })
  source(args$clonality_functions)
  if (!exists("clonality.analysis.mod", mode = "function")) {
    fail("Historical helper did not define clonality.analysis.mod(): %s", args$clonality_functions)
  }
  ref_data <- read.csv(file = args$pfreq, header = TRUE, row.names = "X")
  list(ref_data = ref_data)
}

get_sample_data <- function(data, split) {
  dataCNA2 <- DNAcopy::CNA(assay_matrix(data, "copynumber"), QDNAseq::chromosomes(data), QDNAseq::bpstart(data))
  dataCNA2 <- dataCNA2[!grepl("X|Y", dataCNA2$chrom), ]
  dataCNA <- dataCNA2
  if (split == TRUE) {
    dataCNA$maploc <- dataCNA$maploc / 1000
    dataCNA$chrom <- as.numeric(dataCNA$chrom)
    arms <- Clonality::splitChromosomes(dataCNA$chrom, dataCNA$maploc)
    dataCNA$chrom <- arms
    dataCNA$maploc <- dataCNA$maploc * 1000
  }
  dataCNA
}

LLR2_ref <- function(data, refData, chrom_df, comparison) {
  colnames(refData) <- c("chrom", "pg", "pl", "pn")
  refData$chrom <- as.character(refData$chrom)
  llrData <- clonality.analysis.mod(chrom_df, ptlist = rep(comparison, ncol(data)), pfreq = refData)
  cln <- QDNAseq.dev::clonalityTest(data, sbjctLst = rep(comparison, ncol(data)), pfreq = refData, llrData = llrData)
  data.frame(cln$clonTab)$llr2
}

compute_llr <- function(pairs, qdnaseq_obj, ref_data) {
  values <- rep(NA_real_, nrow(pairs))
  statuses <- rep("computed", nrow(pairs))
  messages <- rep(NA_character_, nrow(pairs))

  for (i in seq_len(nrow(pairs))) {
    sample_one <- pairs$sample1[[i]]
    sample_two <- pairs$sample2[[i]]
    comparison <- paste(sample_one, sample_two, sep = "-")
    sample_obj <- qdnaseq_obj[, c(sample_one, sample_two)]
    result <- tryCatch(
      {
        sample_split_chrom <- get_sample_data(sample_obj, TRUE)
        sample_split_chrom <- sample_split_chrom[sample_split_chrom["chrom"] != "chr21p", ]
        sample_split_chrom <- sample_split_chrom[order(sample_split_chrom[, "chrom"]), ]
        llr <- LLR2_ref(sample_obj, ref_data, sample_split_chrom, comparison)
        if (length(llr) != 1 || is.na(llr)) {
          stop("LLR result was missing or non-scalar", call. = FALSE)
        }
        list(value = as.numeric(llr), status = "computed", message = NA_character_)
      },
      error = function(e) {
        list(value = NA_real_, status = "failed", message = conditionMessage(e))
      }
    )
    values[[i]] <- result$value
    statuses[[i]] <- result$status
    messages[[i]] <- result$message
  }

  data.frame(llr = values, llr_status = statuses, llr_message = messages, stringsAsFactors = FALSE)
}

compare_pcc <- function(results_df, compare_path) {
  if (is.null(compare_path)) {
    return(NULL)
  }
  if (!file.exists(compare_path)) {
    fail("Historical PCC comparison CSV does not exist: %s", compare_path)
  }
  ref <- read.csv(compare_path, stringsAsFactors = FALSE, check.names = FALSE)
  if (!all(c("sample1", "sample2", "pcc") %in% colnames(ref))) {
    fail("Historical PCC comparison CSV must contain sample1, sample2, and pcc columns")
  }
  ref <- ref %>%
    mutate(
      pair_key = pair_key(sample1, sample2),
      pcc_ref = pcc,
      pcc_thresh_ref = if ("pcc_thresh" %in% colnames(.)) pcc_thresh else classify_pcc(pcc_ref)
    ) %>%
    select(pair_key, pcc_ref, pcc_thresh_ref)

  new <- results_df %>%
    mutate(
      pcc_new = pcc,
      pcc_thresh_new = pcc_thresh
    ) %>%
    select(pair_key, pcc_new, pcc_thresh_new)

  merged <- full_join(new, ref, by = "pair_key")
  shared <- merged %>% filter(!is.na(pcc_new), !is.na(pcc_ref))
  data.frame(
    table = basename(compare_path),
    generated_rows = nrow(results_df),
    reference_rows = nrow(ref),
    shared_pairs = nrow(shared),
    missing_in_generated = sum(is.na(merged$pcc_new)),
    missing_in_reference = sum(is.na(merged$pcc_ref)),
    max_abs_pcc_diff = if (nrow(shared) > 0) max(abs(shared$pcc_new - shared$pcc_ref), na.rm = TRUE) else NA_real_,
    pcc_classification_agreement = if (nrow(shared) > 0) sum(shared$pcc_thresh_new == shared$pcc_thresh_ref, na.rm = TRUE) else NA_integer_,
    stringsAsFactors = FALSE
  )
}

write_provenance <- function(path, args, called_info, llr_status) {
  pkg_version <- function(pkg) {
    if (requireNamespace(pkg, quietly = TRUE)) {
      as.character(utils::packageVersion(pkg))
    } else {
      "<not installed>"
    }
  }
  qdnaseq_dev_sha <- "<not installed>"
  if (requireNamespace("QDNAseq.dev", quietly = TRUE)) {
    desc <- utils::packageDescription("QDNAseq.dev")
    remote_sha <- desc$RemoteSha
    qdnaseq_dev_sha <- if (!is.null(remote_sha) && !is.na(remote_sha)) remote_sha else "<not recorded>"
  }

  writeLines(c(
    paste("Cohort:", args$cohort),
    paste("Called RDS:", normalizePath(args$called_rds, mustWork = TRUE)),
    paste("Pairs:", normalizePath(args$pairs, mustWork = TRUE)),
    paste("Output directory:", normalizePath(args$output_dir, mustWork = FALSE)),
    paste("Expected pairs:", args$expected_pairs),
    paste("PCC related threshold:", pcc_related_threshold, "(strict greater than)"),
    paste("PCC inconclusive threshold:", pcc_inconclusive_threshold, "(greater than or equal)"),
    paste("LLR related threshold:", llr_related_threshold, "(strict greater than)"),
    paste("LLR inconclusive threshold:", llr_inconclusive_threshold, "(greater than or equal)"),
    paste("LLR status:", llr_status),
    paste("Observed call states:", paste(called_info$call_values, collapse = ", ")),
    paste("R version:", paste(R.version$major, R.version$minor, sep = ".")),
    paste("QDNAseq version:", pkg_version("QDNAseq")),
    paste("QDNAseq.dev version:", pkg_version("QDNAseq.dev")),
    paste("QDNAseq.dev RemoteSha:", qdnaseq_dev_sha),
    paste("Clonality version:", pkg_version("Clonality")),
    paste("DNAcopy version:", pkg_version("DNAcopy")),
    paste("Biobase version:", pkg_version("Biobase")),
    paste("dplyr version:", pkg_version("dplyr")),
    paste("tidyr version:", pkg_version("tidyr")),
    "",
    "Important interface rule:",
    "Step 2C consumes an explicit Step-2A CGHcall cohort RDS plus explicit pair metadata. It does not run Step 2A, callBins(), Step 2B, or final aggregation."
  ), con = path)
}

args <- parse_args(commandArgs(trailingOnly = TRUE))
dir.create(args$output_dir, recursive = TRUE, showWarnings = FALSE)
tables_dir <- file.path(args$output_dir, "tables")
dir.create(tables_dir, recursive = TRUE, showWarnings = FALSE)

message_line("Step 2C PCC/LLR: %s", args$cohort)
called_info <- validate_called_rds(args$called_rds)
qdnaseq_obj <- called_info$object
pairs <- read_pair_metadata(args$pairs, called_info$sample_ids, args$expected_pairs)
message_line("Pair metadata rows: %d", nrow(pairs))

segment_long <- make_segment_long(qdnaseq_obj)
pcc <- compute_pcc(pairs, segment_long)

llr_state <- llr_availability(args)
if (llr_state$ok) {
  llr_context <- prepare_llr(args)
  set.seed(1337)
  llr_df <- compute_llr(pairs, qdnaseq_obj, llr_context$ref_data)
  llr_status <- if (all(llr_df$llr_status == "computed")) "computed" else "partial_failures"
} else {
  llr_df <- data.frame(
    llr = rep(NA_real_, nrow(pairs)),
    llr_status = rep(llr_state$status, nrow(pairs)),
    llr_message = rep(NA_character_, nrow(pairs)),
    stringsAsFactors = FALSE
  )
  llr_status <- llr_state$status
}

results_df <- pairs %>%
  mutate(
    pcc = pcc,
    pcc_thresh = classify_pcc(pcc),
    llr = llr_df$llr,
    llr_thresh = classify_llr(llr),
    combined_thresh = classify_combined(pcc, llr),
    llr_status = llr_df$llr_status,
    llr_message = llr_df$llr_message
  ) %>%
  relocate(pcc, pcc_thresh, llr, llr_thresh, combined_thresh, llr_status, llr_message, .after = pair_key)

results_output <- file.path(tables_dir, paste0(args$cohort, "_pcc_llr_results.csv"))
summary_output <- file.path(tables_dir, paste0(args$cohort, "_pcc_llr_summary.txt"))
provenance_output <- file.path(tables_dir, paste0(args$cohort, "_pcc_llr_provenance.txt"))
write.csv(results_df, results_output, row.names = FALSE)

comparison <- compare_pcc(results_df, args$compare_pcc_csv)
if (!is.null(comparison)) {
  comparison_output <- file.path(tables_dir, paste0(args$cohort, "_pcc_regression_comparison.tsv"))
  write.table(comparison, comparison_output, sep = "\t", row.names = FALSE, quote = FALSE)
  message_line("Wrote PCC regression comparison: %s", comparison_output)
  print(comparison)
}

summary_lines <- c(
  paste(args$cohort, "PCC/LLR summary"),
  "",
  paste("Expected pairs:", args$expected_pairs),
  paste("Successful PCC pairs:", sum(!is.na(results_df$pcc))),
  paste("PCC range:", paste(signif(range(results_df$pcc, na.rm = TRUE), 6), collapse = " to ")),
  "PCC classification counts:",
  paste(capture.output(print(table(results_df$pcc_thresh, useNA = "ifany"))), collapse = "\n"),
  "",
  paste("LLR status:", llr_status),
  paste("Successful LLR pairs:", sum(results_df$llr_status == "computed" & !is.na(results_df$llr))),
  paste("Failed LLR pairs:", sum(results_df$llr_status == "failed")),
  if (any(!is.na(results_df$llr))) paste("LLR range:", paste(signif(range(results_df$llr, na.rm = TRUE), 6), collapse = " to ")) else "LLR range: NA",
  "LLR classification counts:",
  paste(capture.output(print(table(results_df$llr_thresh, useNA = "ifany"))), collapse = "\n"),
  "Combined PCC/LLR classification counts:",
  paste(capture.output(print(table(results_df$combined_thresh, useNA = "ifany"))), collapse = "\n")
)
if (!is.null(comparison)) {
  summary_lines <- c(
    summary_lines,
    "",
    "PCC historical comparison:",
    paste("Reference rows:", comparison$reference_rows),
    paste("Shared pairs:", comparison$shared_pairs),
    paste("Maximum absolute PCC difference:", comparison$max_abs_pcc_diff),
    paste("PCC classification agreement:", comparison$pcc_classification_agreement)
  )
}
writeLines(summary_lines, summary_output)
write_provenance(provenance_output, args, called_info, llr_status)

message_line("Wrote results: %s", results_output)
message_line("Wrote summary: %s", summary_output)
message_line("Wrote provenance: %s", provenance_output)
