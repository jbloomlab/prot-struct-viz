## Antigenic regions of influenza H1 hemagglutinin

Uncleaved hemagglutinin from influenza A/Victoria/2570/2019, the egg-derived
A(H1N1)pdm09 component of the 2021 vaccine ([PDB 9GSP](https://www.rcsb.org/structure/9GSP)).
HA1 is colored by the classical antigenic site each residue belongs to, taken from Table 2 of
[Wilson et al. (2015), *Virology* 485:252-62](https://pmc.ncbi.nlm.nih.gov/articles/PMC5737639/),
which carries the sites Caton and colleagues mapped on A/PR/8/34 into the numbering of the
2009 pandemic lineage:

- **indigo** — site Sa
- **cyan** — site Sb
- **green** — site Ca1
- **purple** — site Ca2
- **teal** — site Cb
- **light gray** — HA1, not in a defined antigenic region
- **mid gray** — HA2
- **yellow** — N-glycans

Every residue carries its site in HA1 or HA2 numbering — `192_HA1`, `14_HA2` — shown on
mouseover, and drawn into the scene on the antigenic-site residues. The numbering follows
the [H1N1 site numbering map](https://github.com/jbloomlab/flu-seqneut-2026/blob/main/data/nextstrain-prot-titers-tree_data/H1N1_site_numbering_map.tsv).
The protein is drawn as a surface, so each antigenic site reads as a contiguous patch an
antibody could land on. Sa and Sb ring the receptor-binding site at the membrane-distal tip;
Ca1, Ca2 and Cb sit lower on the head, and several of the yellow N-glycans stand over them.

This is an **HA0**: the protease site that would cut HA1 from HA2 is uncut, and the loop
carrying it — HA1 324-327 and HA2 1-6 — is disordered, so it is missing from the view rather
than hidden by it. The deposited coordinates are already the biological trimer, so unlike the
H3 view no assembly is generated in the browser; each label is written once per protomer
instead.
