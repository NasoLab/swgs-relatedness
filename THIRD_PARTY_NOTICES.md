# External components and notices

This snapshot supplies orchestration/adapters and dependency metadata, not
third-party package source, compiled software, reference payloads or images.
Operator acquisition/use must respect the applicable licenses and permissions.

| Component | Evidence | Snapshot treatment |
| --- | --- | --- |
| breakclone matching | Exact revision `712eb202303119588ca10889ca92a721afd0c396` has MIT License, copyright 2022 The Authors | Source remains external; preserve its copyright and full MIT notice if later redistributed |
| UTANOS | Exact revision `ae8edc6464ab7bac0939a886dd7f8beae7a7410b` declares `MIT + file LICENSE`; LICENSE records 2024 utanos authors | Installed package/source/data not bundled; retain applicable MIT notices if distributing it later |
| QDNAseq.dev 0.1 | DESCRIPTION at candidate source revision `8714202a7ca90124adba3ecb0d666cadc23f3d11` says `What license is it under?`; installed-source identity remains incomplete | No package/source/image redistribution clearance |
| Historical PCC/LLR runner and preprocessing | Frozen checksums identify required implementations; ownership/derivative provenance needs confirmation | User-supplied files only; no alternative algorithms substituted |
| CNA_clonality helper and PFREQ | Frozen source revision `bbffb4a15a425ce032537cf95b2d68dbc1d87f15`; applicable grant not confirmed | Code/model remain external and checksum locked |
| R/Bioconductor/native packages | Version/build/license declarations in environment inventories | Metadata only; package/image source and notice obligations require separate review |
| hg38/indexes/PE150 bins | Identities and acquisition limits in the reference manifest | No reference payloads included |

Primary license evidence: [breakclone MIT](https://github.com/argymeg/breakclone/blob/712eb202303119588ca10889ca92a721afd0c396/LICENSE),
[UTANOS DESCRIPTION](https://github.com/Huntsmanlab/utanos/blob/ae8edc6464ab7bac0939a886dd7f8beae7a7410b/DESCRIPTION),
[UTANOS notice](https://github.com/Huntsmanlab/utanos/blob/ae8edc6464ab7bac0939a886dd7f8beae7a7410b/LICENSE),
[QDNAseq.dev DESCRIPTION](https://github.com/tgac-vumc/QDNAseq.dev/blob/8714202a7ca90124adba3ecb0d666cadc23f3d11/DESCRIPTION).
The public source-restoration recipes do not authorize distribution of their
operator-supplied inputs. This notice does not relicense external components.

The intended project MIT license covers only project-owned contributions that
are authorized for distribution. It does not alter any external component's
terms. Legacy Huntsman pipeline attribution is preserved in AUTHORS.md and the
root README; its four retained files still require the authorization in LICENSE.
