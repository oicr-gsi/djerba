"""
The purpose of this file is deal with pre-processing necessary files for the PURPLE plugin.
AUTHOR: Felix Beaudry
"""

import csv
import json
import lets_plot as lp
import logging
import matplotlib.colors as mcolors
import matplotlib.pyplot as plt
import numpy as np
import os
import pandas as pd
import re
import tempfile
import zipfile
from scipy.stats import norm
from plotnine import *

import djerba.plugins.wgts.cnv_purple.constants as pc
from djerba.util.logger import logger
#from djerba.util.subprocess_runner import subprocess_runner
from djerba.util.environment import directory_finder
from djerba.util.image_to_base64 import converter

class purple_processor(logger):

    COPY_STATE_FILE = 'purple_copy_states.json'

    def __init__(self, work_dir, log_level=logging.WARNING, log_path=None):
        self.log_level = log_level
        self.log_path = log_path
        self.logger = self.get_logger(log_level, __name__, log_path)
        self.work_dir = work_dir
        self.r_script_dir = os.path.join(os.path.dirname(__file__), 'r')
        self.data_dir = directory_finder(log_level, log_path).get_data_dir()

  #  def analyze_segments(self, cnvfile, segfile, whizbam_url, purity, ploidy):
  #      dir_location = os.path.dirname(__file__)
  #      centromeres_file = os.path.join(self.data_dir, pc.CENTROMERES)
  #      genebedpath = os.path.join(self.data_dir, pc.GENEBED)
  #      cmd = [
  #          'Rscript', os.path.join(self.r_script_dir, "process_segment_data.r"),
  #          '--outdir', self.work_dir,
  #          '--cnvfile', cnvfile,
  #          '--segfile', segfile,
  #          '--centromeres', centromeres_file,
  #          '--purity', str(purity),
  #          '--ploidy', str(ploidy),
  #          '--whizbam_url', whizbam_url,
  #          '--genefile', genebedpath
  #      ]
  #      runner = subprocess_runner()
  #      result = runner.run(cmd, "segments R script")
  #      return result.stdout.split('"')[1]

    # rewrite analyze_segments in python
    def analyze_segments(self, cnvfile, segfile, whizbam_url, purity, ploidy):
        centromeres_file = os.path.join(self.data_dir, pc.CENTROMERES)
        genebedpath = os.path.join(self.data_dir, pc.GENEBED)
        self.look_at_purity_fit(segfile, purity = purity)
        segs = pd.read_csv(cnvfile, sep="\t")
        segs_whizbam = self.construct_whizbam_links(segs, whizbam_url)
        segs_whizbam.to_csv(os.path.join(self.work_dir, "purple.segments.txt"), sep="\t", index=False)
        centromeres = pd.read_csv(centromeres_file, sep="\t")
        arm_level_calls = self.arm_level_caller_purple(segs, centromeres)
        arm_level_calls.to_csv(os.path.join(self.work_dir, "purple.arm_level_calls.txt"), index=False, header=False)
        
        # Back convert Copy Number profiles to log2 values for plotting in IGV
        segs["ID"] = "purple"
        log2 = segs[["ID", "chromosome", "start", "end", "bafCount"]].copy()
        log2.columns = ["ID", "chrom" ,"loc_start" ,"loc_end" ,"num_mark"]
        log2["seg_mean"] = np.log2(1 + (purity *(segs["copyNumber"] - ploidy)/ploidy))
        log2.to_csv(os.path.join(self.work_dir, "purple.seg"), sep="\t", index=False, header=False)
        log2.to_csv(os.path.join(self.work_dir, "seg.txt"), sep="\t", index=False)

        ##### Getting information for later calculation of LOH in snv_indel plugin  #####
        ### Table with Genes, Minor Allele Copy Number (MACN), Copy Number (CN):
        # Convert chromosomes to genes and display their MACN
        genes_MACN = log2.copy()
        genes_MACN["seg_mean"] = segs["minorAlleleCopyNumber"]
        gene_info = pd.read_csv(genebedpath, sep="\t")
        CN_table = self.pre_proc_loh(genes_MACN, gene_info)

        # Convert chromosomes to genes and display their MACN
        genes_CN = log2.copy()
        genes_CN["seg_mean"] = segs["copyNumber"]
        genes_CN = self.pre_proc_loh(genes_CN, gene_info)

        # Put the tables together to output a table with genes, MACN, CN
        CN_table["local_cn"] = genes_CN["b_allele"]
        
        # Rename the columns
        CN_table.columns = ["Hugo_Symbol", "MACN", "CN"]
        # write to a table
        CN_table.to_csv(os.path.join(self.work_dir, "cn.txt"), index=False, sep="\t")

        # segment plot "seg_CNV_plot.svg"
        chromosomes_incl = list(map(str, range(1,23))) + ["X"]
        segs[['blank','chr']] = segs['chromosome'].str.split('chr',expand=True)
        segs["Chromosome"] = np.where(segs["chr"].isin(chromosomes_incl), segs["chr"], np.NaN)

        highCN=6
        segs["CNt_high"] = np.where(segs["copyNumber"] > highCN, "high", np.NaN)
        fitted_segments_df_sub = segs[["start","end","Chromosome","majorAlleleCopyNumber","minorAlleleCopyNumber","copyNumber","CNt_high"]].copy()
        fitted_segments_df_sub["cent"] = np.NaN

        proc_centromeres = self.process_centromeres(centromeres)
        # combine processed centromeres and fitted_segments_df_sub
        fitted_segments_df_plot = pd.concat([fitted_segments_df_sub.dropna(subset='Chromosome'), proc_centromeres])
        fitted_segments_df_plot['Chromosome'] = fitted_segments_df_plot['Chromosome'].astype(pd.CategoricalDtype(chromosomes_incl, ordered=False))
        fitted_segments_df_plot['copyNumber'] = round(fitted_segments_df_plot['copyNumber'])
        #plot
        breaks = list(range(0,highCN+1,2))

        pseg_path = os.path.join(self.work_dir, "seg_CNV_plot.svg")
        pseg = (
            ggplot(data = fitted_segments_df_plot)
            + geom_hline(yintercept = 2.0 , color="lightgrey", linetype="dotted") 
            + geom_segment(aes(x='start', xend='end', y='copyNumber', yend='copyNumber'), data = fitted_segments_df_plot, color="black",size=2, na_rm = True) 
            + facet_grid(". ~ Chromosome", scales = 'free', space="free")
            + scale_y_continuous(limits=[-0.11,highCN+0.4],breaks=breaks)
            + geom_vline(aes(xintercept = 'start'),data=fitted_segments_df_plot[fitted_segments_df_plot['cent'] == 1],color="lightgrey")
            + geom_point(aes(x='start',y=highCN+0.35), data=fitted_segments_df_plot[fitted_segments_df_plot['CNt_high'] == 'high'], shape='^', size=1)
            + guides(shape='none',alpha='none',linetype='none')
            + labs(y="Copy Number")
            + theme_bw()
            + theme(
                axis_title_x=element_blank(),
                axis_text_x=element_blank(),
                axis_ticks_x=element_blank(),
                panel_grid_minor = element_blank(),
                panel_grid_major = element_blank(),
                strip_background = element_blank(),
                panel_spacing_x = 0.005,
                text = element_text(size = 8),
                axis_title_y = element_text(size = 10)
            )
        )

        pseg.save(pseg_path, height=1.5, width=8)
        image_converter = converter(self.log_level, self.log_path)
        b64txt = image_converter.convert_svg(pseg_path, 'CNV plot')

        # allele specific segment plot "purple.seg_allele_plot.svg"
        fitted_segments_df_plot["A_adj"] = fitted_segments_df_plot["majorAlleleCopyNumber"] + 0.1
        fitted_segments_df_plot["B_adj"] = fitted_segments_df_plot["minorAlleleCopyNumber"] - 0.1

        pseg_allele = (
            ggplot(data = fitted_segments_df_plot)
            + geom_segment(aes(x='start', xend='end', y='A_adj', yend='A_adj'), data = fitted_segments_df_plot, color="#65bc45",size=2, na_rm = True)
            + geom_segment(aes(x='start', xend='end', y='B_adj', yend='B_adj'), data = fitted_segments_df_plot, color="#0099ad",size=2, na_rm = True)
            + facet_grid(". ~ Chromosome", scales = 'free', space="free")
            + scale_y_continuous(limits=[-0.11,highCN+0.11],breaks=breaks)
            + geom_vline(aes(xintercept = 'start'),data=fitted_segments_df_plot[fitted_segments_df_plot['cent'] == 1],color="lightgrey")
            + geom_point(aes(x='start',y=highCN+0.1), data=fitted_segments_df_plot[fitted_segments_df_plot['CNt_high'] == 'high'], shape='^', size=1)
            + guides(shape='none',alpha='none',linetype='none')
            + labs(y="Copy Number")
            + theme_bw()
            + theme(
                axis_title_x=element_blank(),
                axis_text_x=element_blank(),
                axis_ticks_x=element_blank(),
                panel_grid_minor = element_blank(),
                panel_grid_major = element_blank(),
                strip_background = element_blank(),
                panel_spacing_x = 0.005,
                text = element_text(size = 8),
                axis_title_y = element_text(size = 10)
            )
        )

        pseg_allele.save(os.path.join(self.work_dir, "purple.seg_allele_plot.svg"), height=2, width=8)

        return b64txt

   # def consider_purity_fit(self, purple_range_file):
   #     dir_location = os.path.dirname(__file__)
   #     cmd = [
   #         'Rscript', os.path.join(self.r_script_dir, "process_fit.r"),
   #         '--range_file', purple_range_file,
   #         '--outdir', self.work_dir
   #     ]
   #     runner = subprocess_runner()
   #     result = runner.run(cmd, "fit R script")
   #     return result
    # rewrite in python
    def consider_purity_fit(self, purple_range_file):
        range_df = pd.read_csv(purple_range_file, sep="\t", comment='!')
        output = os.path.join(self.work_dir, "purple.range.png")
        
        best_purity = range_df["purity"][0]
        best_ploidy = range_df["ploidy"][0]
        best_score = range_df["score"][0]

        range_after = (range_df.sort_values(by=['purity', 'ploidy'])
                       .assign(
                           absScore=lambda x: x['score'].clip(upper=4),
                           score=lambda x: (abs(x['score'] - best_score) / x['score']).clip(upper=1),
                           ymin=lambda x: (x['purity'] - 0.005),
                           ymax=lambda x: (x['purity'] + 0.005)
                           ))

        range_after["leftPloidy"] = range_df.sort_values(by=['purity', 'ploidy']).groupby('purity')[["ploidy"]].shift(1)
        range_after["rightPloidy"] = range_df.sort_values(by=['purity', 'ploidy']).groupby('purity')[["ploidy"]].shift(-1)

        range_after['xmin'] = range_after['ploidy'] - (range_after['ploidy'] - range_after['leftPloidy']) / 2
        range_after['xmax'] = range_after['ploidy'] + (range_after['rightPloidy'] - range_after['ploidy']) / 2
        range_after['xmin'] = np.where(range_after['xmin'].isna(), range_after['ploidy'], range_after['xmin'])
        range_after['xmax'] = np.where(range_after['xmax'].isna(), range_after['ploidy'], range_after['xmax']) 
        
        max_ploidy = (
            range_after
            .sort_values(by=['purity', 'ploidy'], ascending=[True, False])
            .groupby('purity')
            .first()
            .reset_index()
            ['ploidy']
            .min())
        
        min_ploidy = (
            range_after
            .sort_values(by=['purity', 'ploidy'])
            .groupby('purity')
            .first()
            .reset_index()
            ['ploidy']
            .max())
        
        max_ploidy = max(max_ploidy, best_ploidy)
        min_ploidy = min(min_ploidy, best_ploidy)

        range_after_filter = range_after[(range_after['xmin'] <= max_ploidy) & (range_after['xmax'] >= min_ploidy)]
        range_after_filter['xmax'] = np.minimum(range_after['xmax'], max_ploidy)
        range_after_filter['xmin'] = np.maximum(range_after['xmin'], min_ploidy)
        
        # Create custom gradient
        colors = ["black", "darkblue", "blue", "lightblue", "white", "white"]
        values = [0, 0.1, 0.1999, 0.2, 0.5, 1]
        cmap = mcolors.LinearSegmentedColormap.from_list("custom_cmap", list(zip(values, colors)))

        # Create figure
        fig, ax = plt.subplots(figsize=(10, 6))

        for _, row in range_after_filter.iterrows():
            ax.add_patch(plt.Rectangle((row['xmin'], row['ymin']), 
                                row['xmax'] - row['xmin'], 
                                row['ymax'] - row['ymin'],
                                color=cmap(row['score'])))
        ax.axvline(x=best_ploidy, linestyle='--', linewidth=1, color='k')
        box = dict(boxstyle='round', facecolor='white')
        ax.text(best_ploidy, 1.05, f"{round(best_ploidy, 2)}", fontsize=12, ha='center', bbox=box)
        ax.axhline(y=best_purity, linestyle='--', linewidth=1, color='k')
        ax.text(max_ploidy + 0.4, best_purity, f"{best_purity * 100:.0f}%", fontsize=12, ha='left', va='center', bbox=box)

        ax.set_yticks([0.3, 0.5, 0.75, 1])
        ax.set_yticklabels(["30%", "50%", "75%", "100%"])

        norm = plt.Normalize(0, 1)
        sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm)
        sm.set_array([])

        ax.set_xlabel("Ploidy")
        ax.set_ylabel("Cellularity")

        cbar = plt.colorbar(sm, ax=ax)
        cbar.set_label("Relative\nScore", )
        cbar.set_ticks([0.1, 0.25, 0.5, 1])
        cbar.set_ticklabels(["10%", "25%", "50%", "100%"])

        ax.grid(False)

        plt.tight_layout()
        plt.savefig(output, bbox_inches='tight', backend='Cairo')

    @staticmethod
    def allele_deviation(purity, norm_factor, ploidy, standard_deviation = 0.05, min_standard_deviation_per_ploidy_point = 1.5):
        ploidy_distance_from_integer = 0.5
        if ploidy >= -0.5:
            ploidy_distance_from_integer = abs(ploidy - round(ploidy))
        standard_deviations_per_ploidy = max(min_standard_deviation_per_ploidy_point, purity * norm_factor/ 2/standard_deviation)

        return 2 * norm.cdf(ploidy_distance_from_integer * standard_deviations_per_ploidy) - 1 + max(-0.5-ploidy,0)
    
    def arm_level_caller_purple(self, segs, centromeres, gain_threshold=6, shallow_deletion_threshold=2, seg_perc_threshold=80, baf_min=50):
        """
        Take segment information and turn into chromosome arm level AMP/DEL calls, assuming $seg.perc.threshold is AMP'd or DEL'd
        """
        segs["seg_length"] = segs["end"] - segs["start"]
        ## roughly estimate centromere position 
        ## b/c the annotation has several centromeric regions
        centromeres_rough = centromeres.groupby('chrom').agg(
            cent_start=('chromStart', 'min'),
            cent_end=('chromEnd', 'max'),
            ).reset_index()
        centromeres_rough["cent_length"] = centromeres_rough["cent_end"] - centromeres_rough["cent_start"]
        centromeres_rough["cent_mid"] = round((centromeres_rough["cent_end"] + centromeres_rough["cent_start"]) / 2).astype(int)
        
        arms_n_cents = segs.groupby('chromosome').agg(
            chrom_start=('start', 'min'),
            chrom_length=('end', 'max'),
            ).reset_index().merge(centromeres_rough, how='left', left_on='chromosome', right_on='chrom').drop(columns=["chrom"])
        
        #first arm is always petite (p)
        p_arms = arms_n_cents[['chromosome', 'chrom_start', 'cent_start']].rename(columns={'chromosome':'chrom', 'chrom_start':'arm_start', 'cent_start':'arm_end'})
        p_arms["arm"] = "p"
        p_arms["chrom_type"] = np.where(p_arms["arm_start"] >= p_arms["arm_end"], "acrocentric", "metacentric")

        ## there should be no q-arms longer than chromosome length
        q_arms =arms_n_cents[['chromosome', 'cent_start', 'chrom_length']].rename(columns={'chromosome':'chrom', 'cent_start':'arm_start', 'chrom_length':'arm_end'})
        q_arms['arm'] = "q"

        arm_definitions = pd.concat(
            [p_arms[p_arms["chrom_type"] == "metacentric"].drop(columns=["chrom_type"]), 
             q_arms])
        arm_definitions["arm_length"] = arm_definitions["arm_end"] - arm_definitions["arm_start"]

        segs_dt = segs[["chromosome","start","end","copyNumber","seg_length"]]
        segs_armd = (segs_dt.merge(
            arm_definitions,
            how='inner',
            left_on='chromosome',
            right_on='chrom'
        ).query(
            'start >= arm_start & end <= arm_end & chromosome == chrom'
            ).loc[:, ['chrom', 'arm', 'arm_length', 'copyNumber', 'seg_length', 'arm_start', 'arm_end']])
        segs_armd = segs_armd.rename(columns = {'arm_start':'start', 'arm_end':'end'})
    
        ## use NCCN terminology
        segs_armd["CNA"] = np.where(segs_armd["copyNumber"] < shallow_deletion_threshold, "del", "neutral")
        segs_armd["CNA"] = np.where(segs_armd["copyNumber"] > gain_threshold, "+", segs_armd["CNA"])

        arm_CNA_prop = segs_armd.groupby(['chrom','arm','CNA','arm_length']).agg(
            sum=('seg_length', 'sum'),
            mean=('arm_length', 'mean')
            ).reset_index()
        arm_CNA_prop["seg_perc"] = round((arm_CNA_prop["sum"] / arm_CNA_prop["mean"]) * 100,2)
        arm_CNA_prop = arm_CNA_prop.query('seg_perc > @seg_perc_threshold & CNA != "neutral"').sort_values("seg_perc", ascending=False)
        
        ## assemble annotation from columns
        arm_CNA_prop["annotation"] = arm_CNA_prop["CNA"] + "(" + arm_CNA_prop["chrom"].str.replace("chr", "") + arm_CNA_prop["arm"] + ")"

        return arm_CNA_prop["annotation"].sort_values()
        
    def construct_whizbam_link(self, studyid, tumourid):
        genome = pc.WHIZBAM_GENOME_VERSION
        whizbam_base_url = pc.WHIZBAM_BASE_URL
        seqtype = pc.WHIZBAM_SEQTYPE
        whizbam = "".join((whizbam_base_url,
                           "/igv?project1=", studyid,
                           "&library1=", tumourid,
                           "&file1=", tumourid, ".bam",
                           "&seqtype1=", seqtype,
                           "&genome=", genome
        ))
        return whizbam
    
    def construct_whizbam_links(self, df, whizbam_url):
        if not df.empty:
            df["whizbam"] = whizbam_url + "&chr=" + df["chromosome"].str.replace("chr", "") + \
            "&chrloc=" + df["start"].astype(str) + "- " + df["end"].astype(str)

        return df

  #  def convert_purple_to_gistic(self, purple_gene_file, tumour_id, ploidy):
  #      dir_location = os.path.dirname(__file__)
  #      oncolistpath = os.path.join(self.data_dir, pc.ONCOLIST)
  #      cmd = [
  #          'Rscript', os.path.join(self.r_script_dir, "process_CNA_data.r"),
  #          '--genefile', purple_gene_file,
  #          '--outdir', self.work_dir,
  #          '--oncolist', oncolistpath,
  #          '--tumourid', tumour_id,
  #          '--ploidy', str(ploidy)
  #      ]
  #      runner = subprocess_runner()
  #      result = runner.run(cmd, "CNA R script")
  #      return result
    # rewrite in python
    def convert_purple_to_gistic(self, purple_gene_file, tumour_id, ploidy):
        oncolistpath = os.path.join(self.data_dir, pc.ONCOLIST)
        cna_output = os.path.join(self.work_dir, "purple.data_CNA.txt")
        nondiploid_output = os.path.join(self.work_dir, "data_CNA_oncoKBgenes_nonDiploid.txt")

        if purple_gene_file:
            self.logger.info("Processing CNA data")
            cna, cna_nondiploid = self.pre_process_CNA(purple_gene_file, oncolistpath, tumour_id, ploidy)
            
            # write to files
            cna.to_csv(cna_output, sep="\t", index=False)
            cna_nondiploid.to_csv(nondiploid_output, sep="\t", index=False)
        else:
            self.logger.info("No SEG file input, processing omitted")

    def event_penalty(self, major_allele, minor_allele, ploidy_penalty_factor = 0.4):
        whole_genome_doubling_distance = self.whole_genome_doubling_distance_calculator(major_allele, minor_allele)
        single_event_distance = self.single_event_distance_calculator(major_allele, minor_allele)

        return 1 + ploidy_penalty_factor * min(single_event_distance, whole_genome_doubling_distance)
    
    def look_at_purity_fit(self, segment_file, purity):
        fitted_segments_df = pd.read_csv(segment_file, sep="\t", comment="!")
        fitted_segments_df = fitted_segments_df[(fitted_segments_df["germlineStatus"] == "DIPLOID") & (fitted_segments_df["bafCount"] > 0)].sort_values("majorAlleleCopyNumber")
        fitted_segments_df["Score"] = fitted_segments_df["deviationPenalty"] * fitted_segments_df["eventPenalty"]
        fitted_segments_df["Weight"] = fitted_segments_df["bafCount"]

        max_data = fitted_segments_df[["majorAlleleCopyNumber", "Score"]].loc[fitted_segments_df['majorAlleleCopyNumber'] < 5]
        max_score = np.ceil(max_data["Score"].max())
        min_score = np.floor(max_data["Score"].min())
        maxMajorAllelePloidy = np.ceil(max_data["majorAlleleCopyNumber"].max())
        maxMinorAllelePloidy = maxMajorAllelePloidy - 1 
        sim_ploidy_series = np.round(np.arange(-1, maxMajorAllelePloidy+0.01, 0.01),2)

        purity_df = self.purity_data_frame(self.purity_matrix(purity, sim_ploidy_series), sim_ploidy_series)
        fitted_segments_df["single_event_distance"] = self.single_event_distance_calculator(fitted_segments_df["majorAlleleCopyNumber"], fitted_segments_df["minorAlleleCopyNumber"])
        fitted_segments_df["whole_genome_doubling_distance"] = self.whole_genome_doubling_distance_calculator(fitted_segments_df["majorAlleleCopyNumber"], fitted_segments_df["minorAlleleCopyNumber"])

        # ADD PLOTS
        lp.LetsPlot.setup_html()
        p1 = lp.ggplot(data = purity_df) + \
            lp.geom_tile(lp.aes(x='MajorAllele', y='MinorAllele', fill='Penalty'), width = 3, height = 3) + \
            lp.geom_point(lp.aes(x='majorAlleleCopyNumber', y='minorAlleleCopyNumber', size='Weight'), data=fitted_segments_df, shape=1, stroke=0.3, color="black") + \
            lp.geom_abline(slope = 1, color="black") + \
            lp.scale_x_continuous(limits = [0, min(maxMinorAllelePloidy,4)]) + \
            lp.scale_y_continuous( limits = [0, min(maxMinorAllelePloidy,3)]) + \
            lp.scale_fill_gradientn(colors=["#8b0000","red","orange","yellow", "white"], limits = [min_score, max_score], na_value = "white") + lp.coord_fixed() + \
            lp.theme(panel_grid = lp.element_blank()) + \
            lp.labs(x="Major Allele Ploidy", y="Minor Allele Ploidy", fill="Aggregate\nPenalty",size="BAF\nSupport")
        
        p2 = lp.ggplot() + \
            lp.geom_abline(slope = 1, intercept=1, linetype = 2, color="black", size = 0.5) + \
            lp.geom_point(lp.aes(x='whole_genome_doubling_distance', y='single_event_distance', color='Score', size='Weight'), data=fitted_segments_df, shape=1, stroke=0.3) + \
            lp.scale_color_gradientn(colors=["#8b0000","red","orange","yellow", "white"], limits = [min_score, max_score], na_value = "lightgrey") + \
            lp.labs(x="Whole Genome Doubling Penalty (log)", y="Single Event Penalty (log)", size="BAF Support") + \
            lp.guides(size="none", color="none")+ \
            lp.scale_x_continuous(trans='log10') + \
            lp.scale_y_continuous(trans='log10')

        bunch = lp.GGBunch()
        bunch.add_plot(p1, 0, 0, 600, 500)
        bunch.add_plot(p2, 0, 440, 600, 400)
        lp.ggsave(bunch, "purple.segment_QC.svg", path=self.work_dir)

    
    def major_allele_deviation(self, purity, norm_factor, ploidy, baseline_deviation, major_allele_sub_one_penalty_multiplier = 1 ):
        major_allele_multiplier =1
        if (ploidy >= 0) & (ploidy <= 1):
            major_allele_multiplier = np.maximum(1, major_allele_sub_one_penalty_multiplier * (1-ploidy))
        deviation = major_allele_multiplier * self.allele_deviation(purity, norm_factor, ploidy) + self.sub_minimum_ploidy_penalty(1, ploidy)

        return max(deviation, baseline_deviation)
    
    def minor_allele_deviation(self, purity, norm_factor, ploidy, baseline_devitation):
        deviation = self.allele_deviation(purity, norm_factor, ploidy) + self.sub_minimum_ploidy_penalty(0, ploidy)

        return max(deviation, baseline_devitation)
    
    def pre_process_CNA(self, purple_gene_file, oncolistpath, tumour_id, ploidy, ploidy_multiplier=2.4):
        oncolist = pd.read_csv(oncolistpath, sep="\t")
        raw_gene_data = pd.read_csv(purple_gene_file, sep="\t")
        
        amp = ploidy_multiplier * float(ploidy)
        hmz = 0.5

        oncogenes = oncolist[oncolist["OncoKB Annotated"] == "Yes"]["Hugo Symbol"]
        df_cna_thresh = raw_gene_data[["gene", "minCopyNumber"]].copy()
        df_cna_thresh.rename(columns={"minCopyNumber" : tumour_id}, inplace=True)
        df_cna_thresh[tumour_id] = df_cna_thresh[tumour_id].apply(lambda x: 2 if x > amp else (-2 if x < hmz else 0))

        # subset by genes in oncogenes
        df_cna_thresh_onco = df_cna_thresh[df_cna_thresh["gene"].isin(oncogenes)]
        # subset by nondiploid genes
        df_cna_thresh_onco_nondiploid = df_cna_thresh_onco[df_cna_thresh_onco[tumour_id] != 0]
        df_cna_thresh_onco_nondiploid = df_cna_thresh_onco_nondiploid.rename(columns={"gene":"Hugo_Symbol"})
        df_cna_thresh.insert(0, "Hugo_Symbol", df_cna_thresh["gene"])

        return df_cna_thresh, df_cna_thresh_onco_nondiploid
    
    def pre_proc_loh(self, segments, genebed):
        segments["chrom"] = segments["chrom"].str.replace("chr", "")
        segments["ID"] = "b_allele"
        genebed["b_allele"] = genebed.apply(lambda row: np.min(segments[(segments['chrom'] == row['chrom']) & (segments['loc_start'] <= row['end']) & (segments['loc_end'] >= row['start'])]["seg_mean"]), axis=1)
        a_allele = genebed[["genename", "b_allele"]].copy()

        return a_allele
    
    def process_centromeres(self, centromeres):
        """
        Add some columns to the centromere file so it plots pretty in CNV track
        """
        centromeres[['blank','chr']] = centromeres['chrom'].str.split('chr',expand=True)
        chromosomes_incl = list(map(str, range(1,23))) + ["X"]
        centromeres["Chr"] = np.where(centromeres["chr"].isin(chromosomes_incl), centromeres["chr"], np.NaN)
        centromeres_filter = centromeres.dropna(subset=["Chr"])
        centromeres_sub = centromeres_filter[["chromStart", "chromEnd", "chr"]].copy()
        centromeres_sub.columns = ["start","end","Chromosome"]
        centromeres_sub["majorAlleleCopyNumber"] = np.NaN
        centromeres_sub["minorAlleleCopyNumber"] = np.NaN
        centromeres_sub["CNt_high"] = np.NaN
        centromeres_sub["copyNumber"] = np.NaN
        centromeres_sub["cent"] = 1

        return centromeres_sub

    def purity_data_frame(self, mat, ploidy):
        df = pd.DataFrame(mat)
        df.insert(0, 'MajorAllele', ploidy)
        column_names = ploidy.tolist()
        df.columns = ["MajorAllele"] + column_names
        df_long = df.melt(id_vars=['MajorAllele'], var_name='MinorAllele', value_name='Penalty')
        df_long = df_long.dropna(subset=['Penalty'])
    
        return df_long
    
    def purity_matrix(self, purity, ploidy, baseline_deviation = 0.1):
        result_matrix = np.full(shape=(len(ploidy), len(ploidy)),fill_value=np.nan)
  
        for i in range(len(ploidy)):
            for j in range(i + 1):
                major_ploidy = ploidy[i]
                minor_ploidy = ploidy[j]
                total_penalty = self.event_penalty(major_ploidy, minor_ploidy) * (self.major_allele_deviation(purity, 1, major_ploidy, baseline_deviation) + self.minor_allele_deviation(purity, 1, minor_ploidy, baseline_deviation)) 
                result_matrix[i, j] = total_penalty

        return result_matrix

    def read_purity_ploidy(self, purple_zip):
        tempdir = tempfile.TemporaryDirectory()
        tmp = tempdir.name
        zf = zipfile.ZipFile(purple_zip)
        name_list = [x for x in zf.namelist() if not re.search('/$', x)]
        purple_purity_path = None
        for name in name_list:
            if re.search('purple\.purity\.tsv$', name):
                purple_purity_path = zf.extract(name, tmp)
                break
        if purple_purity_path is None:
            msg = 'Cannot find purity file in ZIP archive {0}'.format(purple_zip)
            self.logger.error(msg)
            raise RuntimeError(msg)
        self.logger.debug('Extracted purity/ploidy to {0}'.format(purple_purity_path))
        with open(purple_purity_path, 'r') as purple_purity_file:
            lines = purple_purity_file.readlines()
        if len(lines) != 2:
            msg = "Data format error: Expected 2 lines in purity/ploidy "+\
                "file {0}, found {1}".format(purple_purity_path, len(lines))
            self.logger.error(msg)
            raise RuntimeError(msg)
        reader = csv.DictReader(lines, delimiter="\t")
        row = next(reader)
        try:
            purity = float(row['purity'])
            ploidy = float(row['ploidy'])
        except ValueError as err:
            msg = "Cannot convert purity/ploidy value to float: {0}".format(err)
            self.logger.error(msg)
            raise RuntimeError(msg) from err
        except KeyError as err:
            msg = "Cannot find purity and/or ploidy column in "+\
                "PURPLE purity file: {0}".format(err)
            self.logger.error(msg)
            raise RuntimeError(msg) from err
        purity_ploidy = {
            pc.PURITY: purity,
            pc.PLOIDY: ploidy
        }
        tempdir.cleanup()
        return purity_ploidy

    def single_event_distance_calculator(self, major_allele, minor_allele):
        single_event_distance = abs(major_allele - 1) + abs(minor_allele - 1)

        return single_event_distance
    
    def sub_minimum_ploidy_penalty(self, min_ploidy, ploidy, major_allele_sub_one_additional_penalty = 1.5):
        penalty = - major_allele_sub_one_additional_penalty * (float(ploidy) - min_ploidy)

        return min(major_allele_sub_one_additional_penalty, max(penalty, 0))
    
    def unzip_purple(self, purple_zip):
        zf = zipfile.ZipFile(purple_zip)
        name_list = [x for x in zf.namelist() if not re.search('/$', x)]
        purple_files = {}
        for name in name_list:
            if re.search('purple\.purity\.range\.tsv$', name):
                purple_files[pc.PURPLE_PURITY_RANGE] = zf.extract(name, self.work_dir)
            elif re.search('purple\.cnv\.somatic\.tsv$', name):
                purple_files[pc.PURPLE_CNV] = zf.extract(name, self.work_dir)
            elif re.search('purple\.segment\.tsv$', name):
                purple_files[pc.PURPLE_SEG] = zf.extract(name, self.work_dir)
            elif re.search('purple\.cnv\.gene\.tsv$', name):
                purple_files[pc.PURPLE_GENE] = zf.extract(name, self.work_dir)
        return purple_files

    def whole_genome_doubling_distance_calculator(self, major_allele, minor_allele):
        whole_genome_doubling_distance = 1 + abs(major_allele - 2) + abs(minor_allele - 2)

        return whole_genome_doubling_distance
    
    def write_copy_states(self, tumour_id):
        """
        Write the copy states to JSON for later reference, eg. by snv/indel plugin
        """
        conversion = {
            0: "Neutral",
            1: "Gain",
            2: "Amplification",
            -1: "Shallow Deletion",
            -2: "Deep Deletion"
        }
        states = {}
        with open(os.path.join(self.work_dir, 'purple.data_CNA.txt')) as in_file:
            reader = csv.DictReader(in_file, delimiter="\t")
            for row in reader:
                gene = row['Hugo_Symbol']
                try:
                    cna = int(row[tumour_id])
                    states[gene] = conversion[cna]
                except (TypeError, KeyError) as err:
                    msg = "Cannot convert unknown CNA code: {0}".format(row[1])
                    self.logger.error(msg)
                    raise RuntimeError(msg) from err
        with open(os.path.join(self.work_dir, self.COPY_STATE_FILE), 'w') as out_file:
            out_file.write(json.dumps(states, sort_keys=True, indent=4))

    def write_purple_alternate_launcher(self, path_info):
        bam_files = path_info.get(pc.BMPP)
        if not path_info.get(pc.MUTECT2) == None:
            vcf_index = ".".join((path_info.get(pc.MUTECT2), "tbi"))
        else:
            vcf_index = None
        purple_paths = {
            "purple.normal_bam": bam_files["whole genome normal bam"],
            "purple.normal_bai": bam_files["whole genome normal bam index"],
            "purple.tumour_bam": bam_files["whole genome tumour bam"],
            "purple.tumour_bai": bam_files["whole genome tumour bam index"],
            "purple.filterSV.vcf": path_info.get(pc.GRIDSS),
            "purple.filterSMALL.vcf": path_info.get(pc.MUTECT2),
            "purple.filterSMALL.vcf_index": vcf_index,
            "purple.runPURPLE.min_ploidy": 0,
            "purple.runPURPLE.max_ploidy": 8,
            "purple.runPURPLE.min_purity": 0,
            "purple.runPURPLE.max_purity": 1
        }
        return purple_paths


