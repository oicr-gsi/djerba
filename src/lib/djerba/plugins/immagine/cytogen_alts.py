
# This file contains the functions to call cytogenetic alterations like monosomy or hyperdiploidy

import numpy as np

def monosomy(chromosome, segment_df):
    """
    A monosomy is defined as:
    >80% of the chromosome Total Copy Number  < 1.2 and minor allele copy number =0  for <50% of that span
    Given a chromosome (ex. chr13), returns True (monosomy) or False (not monosomy)
    segment_df is the purple.segment.tsv file as a dataframe
    """

    # Slice the segment dataframe so it's only the chromosome for which the monosomy is being calculated
    chr_df = segment_df[segment_df['chromosome'] == chromosome].copy()

    # Get the lengths of each segment as well as the total length
    chr_df['length'] = chr_df['end'] - chr_df['start'] + 1
    total_length = chr_df['length'].sum()

    # First, calculate percentage that total copy number < 1.2

    # True if < 1.2, False if >= 1.2
    bool_CN = chr_df['copyNumber'] < 1.2
    #bool_CN = chr_df['majorAlleleCopyNumber'] < 1.2
    # Gets sum of the length for those segments that are True for the above condition
    perc_CN = chr_df.loc[bool_CN, 'length'].sum() / total_length * 100

    # Next, calculate percentage that minor copy number = 0

    # True if == 0, False if != 0
    bool_MACN = chr_df['minorAlleleCopyNumber'] == 0
    # Gets sum of the length for those segments that are True for the above condition
    perc_MACN = chr_df.loc[bool_MACN, 'length'].sum() / total_length * 100

    return bool(perc_CN > 80 and perc_MACN < 50) 


def hyperdiploidy(segment_df):
    """
    Hyperdiploidy is defined as:
    The presence of gains (TCN ≥3) in ≥4 of the canonical hyperdiploid chromosomes: 3, 5, 7, 9, 11, 15, 19, 21
    Given the segment file, returns True if it's hyperdiploid or False if it's not.
    """
    canonical_hyperdiploid_chroms = ['chr3', 'chr5', 'chr7', 'chr9', 'chr11', 'chr15', 'chr19', 'chr21']

    count = 0
    for chromosome in canonical_hyperdiploid_chroms:
        # Make a copy of the segment data that's JUST one chromosome of interest
        chr_df = segment_df[segment_df['chromosome'] == chromosome].copy()

        # Get the lengths of each segment as well as the total length
        chr_df['length'] = chr_df['end'] - chr_df['start'] + 1
        total_length = chr_df['length'].sum()

        # Apply True/False to those segments that meet/don't meet the condition
        bool_CN = chr_df['copyNumber'] >= 2.8 # small tolerance below 3.0
        #bool_CN = chr_df['copyNumber'] >= 3
        #bool_CN = chr_df['majorAlleleCopyNumber'] >= 3
        
        ## Count it as part of the total chromosome count if there is at least one gain in the chromosome
        # Count it as part of the total chromosome count if at least 80% of the chromosome has copy number >=3
        perc_CN = chr_df.loc[bool_CN, 'length'].sum() / total_length * 100
        print(perc_CN)
        if perc_CN > 80:
            count += 1
        #if bool_CN.any():
        #    count += 1
    print(count)
    return bool(count >= 4)

def chromosome_1p_deletion(segment_df):
    """
    Chromosome p deletion is defined as:
    ≥50%�of 1p length has corrected Total Copy Number ≤1.5 and median minor allele copy number indicates
    loss (minor ≤0.5) for the affected span

    Start of centromere (1p acen) is 121700000.
    Let the span of the 1p arm be 0-121700000 (or 1-121700001). Let the length of the 1p-arm be 121700000 bp.
    We'll calculate the percentage with a fixed length as sometimes the segment overlaps the centromere.

    """
    # Slice the segment dataframe so it's only the 1p arm, using 121700001 as the cutoff for the p-arm
    # (The segment file starts numbering at 1, that's why there's a +1)
    chr_df = segment_df[(segment_df['chromosome'] == "chr1") & (segment_df['start'] <= 121700001)].copy()

    # Get the lengths of each segment
    chr_df['length'] = chr_df['end'] - chr_df['start'] + 1
    total_length = 121700000 # fixed 1p length based on cytoBand.txt

    # First, calculate percentage that total copy number <= 1.5

    # True if <= 1.5, False if > 1.5
    bool_CN = chr_df['copyNumber'] <= 1.5
    #bool_CN = chr_df['majorAlleleCopyNumber'] <= 1.5
    # Gets sum of the length for those segments that are True for the above condition
    perc_CN = chr_df.loc[bool_CN, 'length'].sum() / total_length * 100

    # Next, calculate median minor copy number

    # We can't simply compute the median because each segment is a different length.
    # For example, take 2, 4, 5 as an example.
    # The median is 4.
    # But what about 2, 2, 2, 2, 2, 4, 5, 5?
    # Now the median is 2.
    # Therefore, we need to take the lengths of the segments into account.
    # We can do this by computing a weighted median, where the "weights" are the lengths
    # The way you do this is by adding the weights until you reach the half-way weight, and at that value is the weighted median
    values = chr_df['minorAlleleCopyNumber'].to_numpy()
    weights = chr_df['length'].to_numpy()

    # Taken from StackOverflow, an easy way to find the weighted mean via cumulative weights
    i = np.argsort(values)  # indices that would sort the values array from smallest to largest
    c = np.cumsum(weights[i])  # cumulative sum of the weights in the order of the sorted values
    weighted_median = values[i[np.searchsorted(c, 0.5 * c[-1])]]  # value where cumulative weight reaches half the total

    return bool(perc_CN > 80 and weighted_median <= 0.5)


def chromosome_17p_deletion(segment_df):
    """
    Chromosome 17p deletion is defined as:
    >80% of the chromosome Total Copy Number < 1.2 and minor allele copy number = 0 for <50% of that span.


    Start of centromere (17p acen) is 22700000.
    Let the span of the 17p arm be 0-22700000 (or 1-22700001). Let the length of the 17p-arm be 22700000 bp.
    We'll calculate the percentage with a fixed length as sometimes the segment overlaps the centromere.

    """
    # Slice the segment dataframe so it's only the 1p arm, using 22700001 as the cutoff for the p-arm
    # (The segment file starts numbering at 1, that's why there's a +1)
    chr_df = segment_df[(segment_df['chromosome'] == "chr17") & (segment_df['start'] <= 22700001)].copy()

    # Get the lengths of each segment
    chr_df['length'] = chr_df['end'] - chr_df['start'] + 1
    total_length = 22700000 # fixed 1p length based on cytoBand.txt

    # First, calculate percentage that total copy number < 1.2

    # True if < 1.2, False if >= 1.2
    bool_CN = chr_df['copyNumber'] < 1.2
    #bool_CN = chr_df['majorAlleleCopyNumber'] < 1.2
    # Gets sum of the length for those segments that are True for the above condition
    perc_CN = chr_df.loc[bool_CN, 'length'].sum() / total_length * 100

    # Next, calculate percentage that minor copy number = 0

    # True if == 0, False if != 0
    bool_MACN = chr_df['minorAlleleCopyNumber'] == 0
    # Gets sum of the length for those segments that are True for the above condition
    perc_MACN = chr_df.loc[bool_MACN, 'length'].sum() / total_length * 100

    return bool(perc_CN > 80 and perc_MACN < 50)


def biallelic_1p32_deletion(segment_df):
    """
    Chromosome 1p32 biallelic deletion is defined as:
    50% of the 1p32 region had a total copy number near 0-1 and a minor allele copy number of 0.

    The cytoband.txt file givesthe coordinates as:
    ...
    chr1	46300000	50200000	p33	gpos75
    chr1	50200000	55600000	p32.3	gneg
    chr1	55600000	58500000	p32.2	gpos50
    chr1	58500000	60800000	p32.1	gneg
    chr1	60800000	68500000	p31.3	gpos50
    ...

    So start of centromere (1p32.3 gneg) is 50200000.
    End of centromere (1p31 gneg) is 60800000.
    Let the span of the 1p arm be 50200000-60800000 (or 50200001-60800001). 
    Let the length of the 1p32 segment be 60800000-50200000 =  10600000 bp.
    
    We'll calculate the percentage with a fixed length.

    """
    # Slice the segment dataframe so it's only the 1p32 segment
    # (The segment file starts numbering at 1, that's why there's a +1)
    chr_df = segment_df[
        (segment_df['chromosome'] == "chr1") &
        (segment_df['end'] > 50200001) &  
        (segment_df['start'] <= 60800001)  
    ].copy()
    
    # Get the lengths of each segment 
    chr_df['length'] = chr_df['end'] - chr_df['start'] + 1
    total_length = 10600000 # fixed 1p length based on cytoBand.txt 

    # First, calculate percentage that total copy number <= 1
    
    bool_CN = chr_df['copyNumber'] <= 1.5
    # Gets sum of the length for those segments that are True for the above condition
    perc_CN = chr_df.loc[bool_CN, 'length'].sum() / total_length * 100
    

    # Second, calculate percentage that minor allele copy number = 0
    
    bool_MACN = chr_df['minorAlleleCopyNumber'] == 0
    # Gets sum of the length for those segments that are True for the above condition
    perc_MACN = chr_df.loc[bool_CN, 'length'].sum() / total_length * 100

    return bool(perc_CN == 50 and perc_MACN == 50)   
 
    
def monoallelic_1p32_deletion(segment_df):
    """
    Chromosome 1p32 monoallelic deletion is defined as:
    >=50% of the region has a total copy number between 1 and 1.5 and a minor allele copy number approximately equal to 0

    The cytoband.txt file givesthe coordinates as:
    ...
    chr1	46300000	50200000	p33	gpos75
    chr1	50200000	55600000	p32.3	gneg
    chr1	55600000	58500000	p32.2	gpos50
    chr1	58500000	60800000	p32.1	gneg
    chr1	60800000	68500000	p31.3	gpos50
    ...

    So start of centromere (1p32.3 gneg) is 50200000.
    End of centromere (1p31 gneg) is 60800000.
    Let the span of the 1p arm be 50200000-60800000 (or 50200001-60800001). 
    Let the length of the 1p32 segment be 60800000-50200000 =  10600000 bp.
    
    We'll calculate the percentage with a fixed length.

    """
    # Slice the segment dataframe so it's only the 1p32 segment
    # (The segment file starts numbering at 1, that's why there's a +1)
    chr_df = segment_df[
        (segment_df['chromosome'] == "chr1") &
        (segment_df['end'] > 50200001) &  
        (segment_df['start'] <= 60800001)  
    ].copy()
    
    # Get the lengths of each segment 
    chr_df['length'] = chr_df['end'] - chr_df['start'] + 1
    total_length = 10600000 # fixed 1p length based on cytoBand.txt 

    # First, calculate percentage that total copy number is between 1 and 1.5
    
    bool_CN = ((chr_df['copyNumber'] >= 1) & (chr_df['copyNumber'] <= 1.5))
    # Gets sum of the length for those segments that are True for the above condition
    perc_CN = chr_df.loc[bool_CN, 'length'].sum() / total_length * 100
    

    # Second, calculate percentage that minor allele copy number = 0
    
    bool_MACN = chr_df['minorAlleleCopyNumber'] == 0
    # Gets sum of the length for those segments that are True for the above condition
    perc_MACN = chr_df.loc[bool_CN, 'length'].sum() / total_length * 100

    return bool(perc_CN >= 50 and perc_MACN >= 50)

def chromosome_1p_gain_or_amp(segment_df):
    """
    THIS FUNCTION IS NOT DONE YET. Requires clarification from Trevor.
    Chromosome 1p gain is defined as:
    Arm-level gain of 1p call when ≥50% of the arm has total copy number ≥3.0 
    (i.e., gain of at least one extra copy) after purity/ploidy correction

    Chromosome 1p amplification is defined as:
    High-level amplification when a segment (focal or broader) has total copy number ≥6 
    (high confidence) or total copy number ≥4 for moderate amplification
    """
    
    # Slice the segment dataframe so it's only the 1p arm, using 121700001 as the cutoff for the p-arm
    # (The segment file starts numbering at 1, that's why there's a +1)
    chr_df = segment_df[(segment_df['chromosome'] == "chr1") & (segment_df['start'] <= 121700001)].copy()
    # Get the lengths of each segment 
    chr_df['length'] = chr_df['end'] - chr_df['start'] + 1
    total_length = 121700000 # fixed 1p length based on cytoBand.txt 
    # First, calculate percentage that total copy number >= 3.0
    
    # True if >=3.0, False if < 3.0
    bool_CN = chr_df['copyNumber'] >= 3.0
    # Gets sum of the length for those segments that are True for the above condition
    perc_CN = chr_df.loc[bool_CN, 'length'].sum() / total_length * 100
    
    return bool(perc_CN >= 50)

