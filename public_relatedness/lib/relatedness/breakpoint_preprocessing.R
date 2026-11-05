# Exact parsed expressions from internal Huntsman preprocessing revision 39a918d.
rcn_cohort_segs <- ExportBinsQDNAObj(object = rcn_cohort, type = "segments") %>% pivot_longer(cols = !any_of(c("feature", "chromosome", "start", "end")), names_to = "sample_id", values_to = "segmented") %>% arrange(sample_id) %>% dplyr::select(!feature) %>% relocate(sample_id) %>% mutate(segmented = log2(segmented))

rcn_cohort_calls <- ExportBinsQDNAObj(object = rcn_cohort, type = "calls") %>% pivot_longer(cols = !any_of(c("feature", "chromosome", "start", "end")), names_to = "sample_id", values_to = "call") %>% arrange(sample_id) %>% dplyr::select(!feature) %>% relocate(sample_id)

rcn_cohort_collapse <- CopyNumberSegments(rcn_cohort_segs) %>% left_join(y = rcn_cohort_calls, by = join_by(sample_id, chromosome, start)) %>% dplyr::select(!c("end.y")) %>% dplyr::rename(end = "end.x") %>% mutate(cn_call = case_when(call == -1 ~ "loss", call == 1 ~ "gain", call == -2 ~ "deletion", call == 2 ~ "amplification", .default = "neutral"))

df_cohort <- rcn_cohort_collapse %>% filter(sample_id %in% combined_metadata_usable$sample_id) %>% select(sample_id, chromosome, start, end, bin_count, cn_call, sum_of_bin_lengths) %>% mutate(cn_call = case_when(cn_call == "gain" | cn_call == "amplification" ~ "DUP", cn_call == "loss" | cn_call == "deletion" ~ "DEL", .default = cn_call)) %>% filter(cn_call != "neutral") %>% dplyr::rename(c(SampleID = "sample_id", Chr = "chromosome", Start = "start", End = "end", Bins = "bin_count", SVType = "cn_call", 
    Length = "sum_of_bin_lengths"))

