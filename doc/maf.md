# MAF file usage in Djerba

## OICR MAF input format

The basic MAF format was defined by [TCGA](https://www.cancer.gov/about-nci/organization/ccg/research/structural-genomics/tcga). It is a TSV format with 34 required column headers, as described in [this document](https://docs.gdc.cancer.gov/Encyclopedia/pages/Mutation_Annotation_Format_TCGAv2/).

OICR applies additional annotation to MAF files:
- Output from the variantEffectPredictor_2.0.2 workflow has 133 columns.
- The [OncoKB](https://github.com/oncokb/oncokb-annotator/) annotation script adds up to 13 more columns, as described in its [README](https://github.com/oncokb/oncokb-annotator/blob/master/README.md). The script used at OICR is installed under module `oncokb-annotator` in Modulator.
- The total may therefore be up to 146 columns.

## Input MAF columns

Djerba inputs columns by name, not by position. The order of MAF columns is not relevant and additional columns are ignored.

The following column names are used as input for the `MUTATION_EXTENDED` genetic alteration type.

### Required columns

If any of these columns is missing, Djerba will log an error and exit.

- `Hugo_Symbol`: Used as the gene name.
- `Chromosome`: The chromosome is recorded for each gene; also used for `COSMIC_SIGS`.
- `HGVSp_Short`: The name of the changed protein, recorded as `Protein_Change`.
- `t_depth`: Total reads. Used in `Allele_Fraction_Percentile` and `Variant_Reads_And_Total Reads`.
- `t_alt_count`: Variant reads. Used in `Allele_Fraction_Percentile` and `Variant_Reads_And_Total Reads`.
- `Variant_Classification`: Used to compute the `TMB_PER_MB` metric.

### Signature columns

These columns are used to compute the `COSMIC_SIGS` metric. They are not yet required, but will be once the metric is implemented in Djerba.

- `Start_Position`
- `Reference_Allele`
- `Tumor_Sample_Barcode`
- `Allele`

### OncoKB columns: Optional

If these columns are not present, the `OncoKB` and `FDA_Approved_Treatment` fields in Elba config will receive "NA" values.

- `LEVEL_*`. Concatenated and recorded as `FDA_Approved_Treatment`. Permitted levels in OncoKB are: `LEVEL_1, LEVEL_2, LEVEL_3A, LEVEL_3B, LEVEL_4, LEVEL_R1, LEVEL_R2`. Note that not all `LEVEL` fields will necessarily be present.
- `Highest_level`. Recorded as `OncoKB`.

## Output fields

- `Gene`: Value of the `Hugo_Symbol` column.
- `Chromosome`: Value of the `Chromosome` column.
- `Allele_Fraction_Percentile` is defined as `t_alt_count / t_depth`.
- `FDA_Approved_Treatment`: Found from the `LEVEL_` columns, if any.
- `OncoKB`: Found from the `Highest_level` column, if any.
- `Protein_Change`: Value of the `HGVSp_Short` column.
- `Variant_Reads_And_Total Reads` has `t_alt_count` and `t_depth` represented as a string.
- `TMB_PER_MB`: Computed from the `Variant_Classification`, as well as a BED reference.
- `COSMIC_SIGS`: Not yet implemented in Djerba. Existing implementation is an R script [calc_mut_sigs.r](https://github.com/translational-genomics-laboratory/CGI-Tools/blob/main/R/calc_mut_sigs.r), which takes the entire MAF file as input.
