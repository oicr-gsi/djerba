#! /usr/bin/env bash
set -euo pipefail
module load bcftools
# retain PASS variants with VAF >= 10%
MUTATIONS=`bcftools view -f 'PASS' $1 | bcftools filter -i '(FORMAT/AD[0:1]*100)/(FORMAT/AD[0:0]+FORMAT/AD[0:1]) >= 10' | grep -cv '^#'`
MUTATION_RATE=`echo $MUTATIONS/3095978588 | bc -l` # mutation count / genome size
TMB=`echo $MUTATION_RATE*1000000 | bc -l`
echo $TMB
