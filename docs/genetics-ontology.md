# Western hognose morph ontology / 西部猪鼻蛇形态词表

The machine-readable source is [`data/ontology.json`](../data/ontology.json). It separates a **locus/trait** from a **combination nickname**. The historical course labels are mapped but retain `unverified` provenance; mapping a column name does not validate any individual row.

| Breeder name | Canonical components | Interpretation |
| --- | --- | --- |
| Anaconda / Superconda | `anaconda:heterozygous` / `anaconda:homozygous` | Two states of one incomplete-dominant locus, not two independent genes. |
| Arctic / Super Arctic | `arctic:heterozygous` / `arctic:homozygous` | Two states of one incomplete-dominant locus. |
| Sunburst | `sable:expressed` + `albino:expressed` | Both recessive traits expressed. |
| Snow | `albino:expressed` + `axanthic:expressed` | Both recessive traits expressed. |
| Yeti / Super Yeti | Snow + Anaconda / Snow + Superconda | Same Anaconda locus at one/two copies. |
| Snowburst | Sable + Albino + Axanthic | Three expressed recessive traits. |
| Extreme Red Sunburst | Sunburst + `extreme_red:line_trait` | Extreme Red is treated as a polygenic/line trait, not one Mendelian allele. |
| Toxic | Axanthic + Toffee Belly | Hognose Hub-reported combination of two expressed recessive traits. |
| Mai Tai | Sable + Toffee Belly | Hognose Hub-reported combination; Mai Tai Anaconda adds heterozygous Anaconda. |
| Stormcloud (also “Storm Cloud”) | Axanthic + Sable | Hognose Hub-reported combination of two expressed recessive traits. |
| Moonstone | Lavender + homozygous Arctic | Hognose Hub-reported combination; Arctic state is recorded separately from recessive Lavender. |
| Coral | Albino + Lavender | Hognose Hub-reported combination of two expressed recessive traits. |

The catalogue also includes Lemon Ghost, Pink Pastel Albino, Lucy, Chocolate, Skull Face and Diablo eyes. Their identity/inheritance is **unresolved in this project's evidence**. They remain historical labels rather than silently acquiring a made-up gene. `Lucy` is not automatically equated with an independently verified leucistic locus; `Chocolate` is not automatically equated with Swiss Chocolate.

**White Wall is not a genetic locus.** The old workbook column is preserved as a historical annotation and mapped to the separate `phenotype_descriptors.white_wall` entry. It describes a visible pale/white lateral feature along the belly, which can appear in descriptions of Anaconda-patterned snakes; seeing it does not establish Anaconda or another genotype. Accordingly it is excluded from the canonical genetic traits and the trait-classifier outputs. The [Hognose Wiki Anaconda description](https://hognose.fandom.com/wiki/Anaconda) mentions white walls as an associated visible feature, while [Reptifit's Anaconda guide](https://www.reptifit.nl/en/collection) describes the gene as a pattern-affecting mutation. Neither turns “White Wall” into an independent gene.

## Decision rules / 判断规则

1. Record the *exact source claim* and its provenance: individual ID, breeder/owner, lineage or genetic test, image rights, reviewer, date and URL. A sales title alone is a lead.
2. Normalize a verified composite nickname into its listed constituent traits. Keep the nickname for display and the source wording for audit.
3. Record zygosity explicitly. Two-copy Superconda is not `Anaconda + Superconda`; a carrier (`het Albino`) is not an expressed Albino photo label.
4. A photo can suggest visible colour and pattern. It cannot prove hidden recessive carriers, lineage, or a newly discovered genetic mutation. An expert visual review is stored as `claim_scope=phenotype`; genotype claims require breeding/genetic evidence.
5. For a potential new trait, mark `unknown_candidate` with a description and images. Seek independent individuals, documented lineage or genetic tests, repeatable appearance across lighting/age, and expert review before adding a named locus. A low model score or large embedding distance can trigger review, never an automatic gene name.
6. Do not read independent sigmoid scores as a softmax partition. A snake can express multiple traits. A calibrated claim of “90% genotype probability” requires separate calibration and validation data.

The breeder's [collection descriptions](https://www.reptifit.nl/en/collection) document Anaconda/Superconda, Arctic/Super Arctic, Snow, Yeti and Snowburst; the [Extreme Red Sunburst listing](https://www.reptifit.nl/en/available/western-hognose-snake-extreme-red-sunburst/) names Sable + Albino and calls Extreme Red polygenic. The Hognose Hub Genetics Lab describes [Toxic](https://hognosehub.com/genetics-lab/toxic), [Mai Tai](https://hognosehub.com/genetics-lab/mai-tai), [Stormcloud](https://hognosehub.com/genetics-lab/stormcloud), [Moonstone](https://hognosehub.com/genetics-lab/moonstone) and [Coral](https://hognosehub.com/genetics-lab/coral) combinations; these aliases retain those source URLs in the machine-readable ontology. These breeder and community references are terminology evidence, not molecular proof of every named locus or evidence about a particular photographed snake. MorphMarket/Instagram listings are leads until individual evidence and image-use rights are checked.

## Future naming format

Prefer `trait_id:state` in data, with an English display name and Chinese translation. Aliases store ordered canonical components and source URLs. Unknown candidates live in review records, outside training labels. Keep aliases versioned: if a breeder's name later proves ambiguous, add a source-scoped alias rather than rewriting previous samples.
