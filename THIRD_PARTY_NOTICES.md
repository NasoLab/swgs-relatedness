# External components and notices

This snapshot supplies project scientific source, orchestration/adapters and
dependency metadata, plus the reviewed upstream MIT matcher source. No installed
package, compiled software, reference payload or image is included.
Operator acquisition/use must respect the applicable licenses and permissions.

| Component | Evidence | Snapshot treatment |
| --- | --- | --- |
| breakclone matching | Exact revision `712eb202303119588ca10889ca92a721afd0c396` has MIT License, copyright 2022 The Authors | Exact copynumber.R is included under public_relatedness/vendor/breakclone with the full upstream MIT notice |
| UTANOS | Exact revision `ae8edc6464ab7bac0939a886dd7f8beae7a7410b` declares `MIT + file LICENSE`; LICENSE records 2024 utanos authors | Installed package/source/data not bundled; retain applicable MIT notices if distributing it later |
| QDNAseq.dev 0.1 | DESCRIPTION at candidate source revision `8714202a7ca90124adba3ecb0d666cadc23f3d11` says `What license is it under?`; installed-source identity remains incomplete | No package/source/image redistribution clearance |
| Project PCC/LLR runner and historical preprocessing | Richard Corbett's cohort-reporting runner and Branden Lynch's internal Huntsman preprocessing; original and packaged hashes in scientific_sources.json | Runner and four selected preprocessing expressions bundled under project MIT; contributor credits retained; automatically located |
| CNA_clonality helper and PFREQ | Frozen source revision `bbffb4a15a425ce032537cf95b2d68dbc1d87f15`; applicable grant not confirmed | Code/model remain external and checksum locked |
| R/Bioconductor/native packages | Version/build/license declarations in environment inventories | Metadata only; package/image source and notice obligations require separate review |
| hg38/indexes/PE150 bins | Identities and acquisition limits in the reference manifest | No reference payloads included |

Primary license evidence: [breakclone MIT](https://github.com/argymeg/breakclone/blob/712eb202303119588ca10889ca92a721afd0c396/LICENSE),
[UTANOS DESCRIPTION](https://github.com/Huntsmanlab/utanos/blob/ae8edc6464ab7bac0939a886dd7f8beae7a7410b/DESCRIPTION),
[UTANOS notice](https://github.com/Huntsmanlab/utanos/blob/ae8edc6464ab7bac0939a886dd7f8beae7a7410b/LICENSE),
[QDNAseq.dev DESCRIPTION](https://github.com/tgac-vumc/QDNAseq.dev/blob/8714202a7ca90124adba3ecb0d666cadc23f3d11/DESCRIPTION).
The public source-restoration recipes do not authorize distribution of their
operator-supplied inputs. This notice does not relicense external components.

The project MIT license applies to project-owned code, including retained
internal Huntsman research-pipeline components. It does not alter any external
component's terms. Huntsman group acknowledgement and contributor credits are
preserved in AUTHORS.md and the root README; these credits do not assign
copyright ownership. No external implementation, package, reference or image is
relicensed by LICENSE.

Phase 5 bundles the exact MIT breakclone copynumber.R at the revision above;
its copyright 2022 The Authors and full notice are preserved in vendor/breakclone.
Only getHit/calculateMaxGap are evaluated by the existing adapter; frequency-
weighted pair_score remains unused. The modified CNA_clonality helper is not
bundled: eleven functions match GPL-3 Clonality 1.47.0 (Irina Ostrovnaya), while
calc.freq differs in the upstream helper recorded under jurriaanjanssen. Its
modification terms must be established before any vendoring. Public acquisition
of exact bytes does not change its licensing. QDNAseq.dev remains an external
package with the recorded placeholder license. None is relicensed as project MIT.
