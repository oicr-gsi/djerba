while read directories
do
Rscript CNV_summary.R -f ${dirs}/* >>PGA.all.txt
done < directories.txt

Rscript CNV_all.R 