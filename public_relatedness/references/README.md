# Reference identity and acquisition

This directory contains metadata only. No FASTA, indexes, annotations or PFREQ
payloads are bundled, downloaded, regenerated or redistributed by this phase.
The machine-readable authority is [manifest.json](manifest.json). All SHA256
values below were measured from existing local files, except the already-frozen
PFREQ hash retained from its established authority. The supplied PE150 hash was
independently confirmed against the retained annotation.

| Expected filename | Local parameter | SHA256 |
| --- | --- | --- |
| `GCA_000001405.15_GRCh38_no_alt_analysis_set.fna` | `reference` | `9cce8b926416dd96b152deea85188495b75f7ac8d634cc723a017067be8702b7` |
| `GCA_000001405.15_GRCh38_no_alt_analysis_set.fna.0123` | `reference` + `.0123` | `8ba8b25121ad5f0a59d72ae02882dddd86f272dfaa00f58db70557b02aa74f86` |
| `GCA_000001405.15_GRCh38_no_alt_analysis_set.fna.amb` | `reference` + `.amb` | `937fb382f79b8382cb3be2f13dc88d29147661919bb8c398d307b1bcc52c0890` |
| `GCA_000001405.15_GRCh38_no_alt_analysis_set.fna.ann` | `reference` + `.ann` | `71b231aee7bd25800756f1165d2cf9dd41501ca248a147de70c2bb83f2849f1c` |
| `GCA_000001405.15_GRCh38_no_alt_analysis_set.fna.bwt.2bit.64` | `reference` + `.bwt.2bit.64` | `3021440b3f10dc91f92af368ba0503806dfae813cd5bcf053fa606a585e2c454` |
| `GCA_000001405.15_GRCh38_no_alt_analysis_set.fna.pac` | `reference` + `.pac` | `1b598382ddcf7e4ce8b120b22ba4c66ec837795e22b5a9caa21cc61797a6561a` |
| `1000g_hg38_bins_500kbp_PE150.rds` | `pe150_bins` | `1d62a94b9a88845978c7bf709d00b35b0f3b1243ef894b442c3ac2861a23337c` |
| `pfreq_lusc_tcga_split.csv` | `pfreq` | `582b6b53c4a4f70149b115c504685f24e983c522d63c1cb42c25a90db103e04f` |

## hg38 FASTA and BWA-MEM2 sidecars

Historical Nextflow parameter logs identify the GRCh38 no-alt analysis-set
FASTA shown above. Its canonical acquisition location is under NCBI accession
[GCA_000001405.15](https://ftp.ncbi.nlm.nih.gov/genomes/all/GCA/000/001/405/GCA_000001405.15_GRCh38/seqs_for_alignment_pipelines.ucsc_ids/).
The original download receipt/compressed-file checksum was not recovered; the
canonical FTP location could not be independently fetched in this audit.
A future approved acquisition should retrieve that exact no-alt archive,
verify upstream checksums, decompress it and compare the **uncompressed** SHA256
above. Do not replace it with the full/ALT/decoy assembly or merely another file
labelled hg38 while claiming byte-identical reproduction.

Supply `--reference` as the FASTA path. All five BWA-MEM2 sidecars must be adjacent
and use that full FASTA basename plus the listed suffix. The expected generation
command family is `bwa-mem2 index` using version 2.2.1; the precise historical
build invocation, binary/hardware receipt and generation environment remain
unrecovered. Existing sidecar hashes are the reproducible identity boundary.
No indexing was performed. Regenerating indexes requires separate approval and
comparison against the recorded assets; ordinary BWA indexes are not substitutes.

The FASTA basename may contain dots, including the accession version `.15`.
Renaming an asset is acceptable only if its contents retain the required hash
and every sidecar follows the renamed FASTA consistently.

## QDNAseq PE150, hg38, paired-end, 500 kb

Expected file: `1000g_hg38_bins_500kbp_PE150.rds`.
Parameter: `--pe150_bins`; the approved SHA256 is also the default
`--pe150_bins_sha256`. Non-stub manifest preflight requires both the approved
checksum identity and matching bytes. Users cannot substitute another annotation
by supplying its own matching checksum. PE50 is never accepted as equivalent.

The established annotation family uses QDNAseq hg38 bins, base/GC composition,
mappability, blacklist overlap and residuals from 1000 Genomes control profiles.
The exact PE150 generator, package environment, control accessions and input
mappability/blacklist hashes are not fully established. A nearby local generator
explicitly targets 50-bp inputs and outputs PE50; it is **not** a reproducible
PE150 build recipe. The retained PE150 asset must be acquired from its authorized
owner, with permission and provenance, until those receipts are recovered.
Do not regenerate annotations under this installation workflow.

## Frozen TCGA LUSC PFREQ

Expected file: `pfreq_lusc_tcga_split.csv`; parameter `--pfreq`. Its established
source is `reference/pfreq_lusc_tcga_split.csv` at
[CNA_clonality revision bbffb4a](https://github.com/tgac-vumc/CNA_clonality/tree/bbffb4a15a425ce032537cf95b2d68dbc1d87f15/reference).
This is a frozen chromosome-arm frequency model, not an incoming-cohort training
step. Exact original training/filtering/accession receipts and redistribution
permission remain unresolved. Obtain an authorized byte-identical copy; never
regenerate PFREQ from the user cohort to make installation convenient.

## Redistribution boundary

No distribution clearance is inferred from a checksum, a public URL or the
license of the generating software. See [LICENSING.md](../LICENSING.md) for
project, source-code and derived-data permissions. The reference manifest
records asset-specific source/generation uncertainty and local configuration
parameters. Missing generation details are release blockers, not guessed pins.
