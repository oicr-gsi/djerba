from djerba import __version__
import djerba.core.constants as core_constants

##LINKS
ARRIBA_LINK="https://github.com/suhrig/arriba"
BWAMEM_LINK="https://bio-bwa.sourceforge.net/"
CONSENSUSCRUNCHER_LINK="https://github.com/pughlab/ConsensusCruncher"
DJERBA_LINK="https://github.com/oicr-gsi/djerba"
GATK_LINK="https://gatk.broadinstitute.org/hc/en-us/sections/360008481611-4-1-6-0"
ICHORCNA_LINK="https://github.com/broadinstitute/ichorCNA"
MANE_LINK="https://www.ncbi.nlm.nih.gov/refseq/MANE/#Select"
MAVIS_LINK="https://github.com/bcgsc/mavis"
MICROSATELLITE_LINK="https://www.sciencedirect.com/science/article/pii/S1672022920300218"
MRDETECT_LINK="https://pubmed.ncbi.nlm.nih.gov/32483360/"
MUTECT2_LINK="https://gatk.broadinstitute.org/hc/en-us/articles/5358911630107-Mutect2"
NCCN_OVARIAN_LINK="https://www.nccn.org/professionals/physician_gls/pdf/ovarian.pdf"
NCCN_PCM_LINK="https://www.nccn.org/professionals/physician_gls/pdf/myeloma.pdf"
ONCOKB_LINK="https://api.oncokb.org/oncokb-annotator/gene-annotation"
PICARD_LINK="https://gatk.broadinstitute.org/hc/en-us/articles/360037052812-MarkDuplicates-Picard-"
PURPLE_LINK="https://github.com/hartwigmedical/hmftools/blob/master/purple/README.md"
REFERENCE_GENOME_LINK="https://www.ncbi.nlm.nih.gov/assembly/GCF_000001405.38/"
RSEM_LINK="https://github.com/deweylab/RSEM"
STAR_LINK="https://github.com/alexdobin/STAR"
STARFUSION_LINK="https://github.com/STAR-Fusion/STAR-Fusion/wiki"
VARIANTEFFECTPREDICTOR_LINK="https://useast.ensembl.org/info/docs/tools/vep/index.html"

##VERSIONS
ARRIBA_VERSION="2.4.0"
BWAMEM2_VERSION="2.2.1"
BWAMEM1_VERSION="0.7.17"
CONSENSUSCRUNCHER_VERSION=""
DJERBA_VERSION=__version__
GATK_VERSION="4.2.2.0"
ICHORCNA_VERSION=""
ILLUMINA_VERSION="NovaSeq X Plus v1.3"
TAR_ILLUMINA_VERSION="NextSeq 2000"
MANE_VERSION="1.0"
MAVIS_VERSION="2.2.6"
MICROSATELLITE_VERSION="1.2.0"
MICROSATELLITE_CUSTOM_SITES="1,900,495"
MRDETECT_VERSION="1.0"
MUTECT2_VERSION="4.1.6.0"
NCCN_OVARIAN_VERSION="2025.2"
NCCN_PCM_VERSION="2026.1"
PICARD_VERSION="2.21.2"
PURPLE_VERSION="3.8.1"
# see pwgs.case_overview plugin for PWGS assay version
REFERENCE_GENOME_VERSION="GRCh38.p12"
RSEM_VERSION="1.3.3"
STAR_VERSION="2.7.10b"
STARFUSION_VERSION="1.8.1"
SUPPLEMENT_DJERBA_VERSION="0.1"
VARIANTEFFECTPREDICTOR_VERSION="105.0"

def make_component_info_string(components):
    # convenience method to stringify the versions dictionary at Mako render time
    # also insert URLs if available
    component_names = sorted(list(components.keys()))
    info_list = []
    for name in component_names:
        url = components[name][core_constants.URL_KEY]
        version = components[name][core_constants.VERSION_KEY]
        if url == None:
            entry = '{0} ({1})'.format(name, version)
        else:
            entry = '<a href={0}>{1}</a> ({2})'.format(url, name, version)
        info_list.append(entry)
    return ', '.join(info_list)
