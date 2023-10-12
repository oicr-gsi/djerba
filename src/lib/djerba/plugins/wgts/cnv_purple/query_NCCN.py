import os
import json
from collections import Counter

BIOMARKER_FILE = "entire_biomarkers.pretty.json"
BIOMARKER_PATH='Documents/data'

def find_aberrations(disease_biomarker):
    related_aberrations = {}
    deletions = find_deletions(disease_biomarker["NCCNRecommendation"] + disease_biomarker["Notes"])
    if len(deletions) > 0:
        related_aberrations["deletions"]= deletions
    translocations = find_translocations(disease_biomarker["NCCNRecommendation"]+disease_biomarker["Notes"])
    if len(translocations) > 0:
        related_aberrations["translocations"]= translocations
    return(related_aberrations)

def find_amplifications(NCCN_string):
    ## NOT FUNCTIONAL
    split_string = NCCN_string.split("+")
    appended_amps = []
    for candidate_string in split_string:
        print(candidate_string)
        if len(candidate_string) > 0 and len(candidate_string) < 4:
            if candidate_string[0].isnumeric():
                amp = ""
                first_character = candidate_string[0]
                if len(candidate_string) == 1:
                    amp = first_character
                if len(candidate_string) == 2:
                    if candidate_string[1].isnumeric():
                        chromosome_number = first_character + candidate_string[1]
                        amp = chromosome_number
                    elif candidate_string[1].isalpha():
                        chromosome_arm = candidate_string[1]
                        amp = chromosome_number + chromosome_arm
                if len(candidate_string) == 3:
                    if candidate_string[2].isalpha():
                        chromosome_number = first_character + candidate_string[1]
                        chromosome_arm = candidate_string[2]
                        amp = chromosome_number + chromosome_arm
                appended_amps.append("+(" + amp + ")")
    return(appended_amps)

def find_deletions(NCCN_string):
    split_string = NCCN_string.split("del")
    appended_deletions = []
    for candidate_string in split_string:
        if len(candidate_string) > 0:
            if candidate_string[0] == "(" or (candidate_string[0] == " " and candidate_string[1] == "("):
                candidate_split = candidate_string.split("(")
                candidate_string = candidate_split[1].split(")")
                appended_deletions.append("del(" + candidate_string[0] + ")")
    return(appended_deletions)

def find_translocations(NCCN_string):
    split_string = NCCN_string.split("t(")
    appended_translocations = []
    for candidate_string in split_string:
        if len(candidate_string) > 0:
            if candidate_string[0].isnumeric():
                candidate_split = candidate_string.split(")")
                appended_translocations.append("t(" + candidate_split[0] + ")")
    return(appended_translocations)

def get_disease_short_name(GuidelinePages):
    GuidelinePages_split = GuidelinePages["Name"].split()
    GuidelinePages_split = GuidelinePages_split[0].split("-")
    return(GuidelinePages_split[0])

def make_biomarker_dictionary(biomarker_list):
    biomarker_disease_dict = {}
    for biomarker in biomarker_list:
        disease_list = []
        disease_short_list = []
        results = {}
        for disease in diseases:
            for disease_biomarker in disease["Biomarker"]:
                for abnormality in disease_biomarker["MolecularAbnormalities"]:
                    if abnormality["Name"] == biomarker:
                        disease_list.append(disease["DiseaseName"])
                        for GuidelinePages in disease_biomarker["GuidelinePages"]:
                            disease_short_list.append(get_disease_short_name(GuidelinePages))
                        related_aberrations = find_aberrations(disease_biomarker)
                        if len(related_aberrations) > 0:
                            results[disease["DiseaseName"]] = related_aberrations
        results["disease_set"] = list(set(disease_list))
        results["disease_short_set"] = sorted(list(set(disease_short_list)))
        biomarker_disease_dict[biomarker] = results
    return(biomarker_disease_dict)
        
def make_diseases(biomarker_path):
    biomarker_path = os.path.join(biomarker_path, BIOMARKER_FILE)
    with open(biomarker_path, 'r') as f:
        data = json.load(f)
    guidelines = data["Guidelines"]
    diseases = []
    for i in guidelines:
        diseases.append(i["Diseases"])
    subdiseases = []
    for disease in diseases:
        for subdisease in disease:
            subdiseases.append(subdisease)
    return(subdiseases)

def tally_biomarkers(diseases, print_counts=True):
    biomarkers = []
    for disease in diseases:
        for biomarker in disease["Biomarker"]:
            for abnormality in biomarker["MolecularAbnormalities"]:
                biomarkers.append(abnormality["Name"])
    if print_counts:
        counts = Counter(sorted(biomarkers))
        for key in counts:
            print("{}: {}".format(key, counts[key]))
    return(sorted(list(set(biomarkers))))

diseases = make_diseases(BIOMARKER_PATH)
biomarker_list = tally_biomarkers(diseases)
biomarker_disease_dict = make_biomarker_dictionary(biomarker_list)

json_formatted_str = json.dumps(biomarker_disease_dict, indent=2)
print(json_formatted_str)

REARRANGEMENT_LIST= [
    "translocation",
    "rearrangement",
    "inversion",
    "deletion" ,
    "gain",
    "Trisomy",
    "aberration",
    "hromosom", #chromosome, Chromosomal etc
    "duplication",
    "ploid",
    "karyotype",
    "Genomic",
    "copy number",
    "amplification",
    "LOH",
    "MSI",
    "inv(",
    "Homologous recombination deficiency",
    "mismatch repair",
    "Genetic alterations",
    "abn(",
    "Copy number alterations",
    "Gain",
    "Disomy/Monosomy"
]

INFECTION_LIST= [
    "irus",
    "infection",
    "viral",
    "Hepatitis",
    "HPV",
    "HIV",
    "EBV",
    "CMV",
    "Helicobacter pylori"
]

IMMUNE_TYPE = [
    "mmunopheno",
    "CD4",
    "HLA type",
    "IGHV (Ig heavy chain variable region) sequencing",
    "IL6"
]

EXPRESSION_LIST = [
    "mRNA",
    "expression",
    "methylation",
    "Methylated",
    "HIstologic abnormalities"
]

BLOOD_LIST = [
    "plasma",
    "Plasma",
    "blood",
    "erum",
    "protein",
    "Blood",
    "Minimal residual disease",
    "Albumin",
    'secretion',
    'Aldosterone/renin activity',
    'B2M (beta-2-microglobulin) level',
    "Congenital neutropenia",
    "Diamond-Blackfan anemia",
    "G6PD deficiency",
    "Hypercortisolemia"
]

MUTATION_LIST = [
    "iallelic",
    "mutation" ,
    "Mutation",
    "inactivation",
    "gene polymorphisms",
    "RASopathies",
        "fusion",
]


mutations_group = []
expression_group = []
translocation_rearrangement_group = []
infection_group = []
secretion_group = []
syndrome_group = []
immuno_group = []
blood_group = []
ungrouped = []
for biomarker in biomarker_list:
    grouped=False
    for infection_flag in INFECTION_LIST:
        if infection_flag in biomarker:
            infection_group.append(biomarker)
            grouped=True
    for chromosome_flag in REARRANGEMENT_LIST:
        if chromosome_flag in biomarker:
            translocation_rearrangement_group.append(biomarker)
            grouped=True
    for mut_flag in MUTATION_LIST:
        if mut_flag in biomarker:
            mutations_group.append(biomarker)
            grouped=True
    for expression_flag in EXPRESSION_LIST:
        if expression_flag in biomarker:
            expression_group.append(biomarker)
            grouped=True
    if "yndrome" in biomarker:
        syndrome_group.append(biomarker)
        grouped=True
    for immuno_flag in IMMUNE_TYPE:
        if immuno_flag in biomarker:
            immuno_group.append(biomarker)
            grouped=True
    for blood_flag in BLOOD_LIST:
        if blood_flag in biomarker:
            blood_group.append(biomarker)
            grouped=True
    if grouped == False:
        print(biomarker)
        ungrouped.append(biomarker)


ungrouped_dict = make_biomarker_dictionary(translocation_rearrangement_group)
json_formatted_str = json.dumps(ungrouped_dict, indent=2)
print(json_formatted_str)


###### VERSION 1 ####

import json
import re
import argparse
import requests

CLEANR = re.compile('<.*?>') 

API_ADDRESS = 'https://www.nccn.org/webservices/Products/Api/Biomarker/GetBiomarkersByGuidelineName/'


def retrieve_NCCN_online(cancer_name, access_key = '39c9f806-5288-4e69-a373-ea17aa9df924'):
        full_NCCN_url = "/".join([API_ADDRESS, access_key, cancer_name])
        res_specific_biomarkers = requests.get(full_NCCN_url)
        specific_biomarkers = json.loads(res_specific_biomarkers.text)
        guidelines = specific_biomarkers['Guidelines'][0] #shouldn't be any other guidelines
        return(guidelines[0])

def retrieve_NCCN_json(cancer_name, input_file_location='entire_biomarkers.json'):
        with open(input_file_location, 'r') as entire_biomarkers_file:
                entire_biomarkers = json.load(entire_biomarkers_file)
                entire_biomarkers = entire_biomarkers['Guidelines']
                guidelines = [ x for x in entire_biomarkers if x['Name'] == cancer_name ]
        return(guidelines[0])

def pull_out_key_attributes(guidelines, cancer_type):
        disease_names = [ disease['DiseaseName'] for disease in guidelines['Diseases'] ]
        guidelines = guidelines['Diseases']
        for disease in disease_names:
                guidelines_by_disease = [x for x in guidelines if x['DiseaseName'] == disease]
                biomarkers_by_disease = guidelines_by_disease[0]['Biomarker']
                for biomarker in biomarkers_by_disease:
                        process_biomarker(biomarker, cancer_type, disease)

def process_biomarker(biomarker, cancer_type, disease):
        testDetects_list = biomarker['TestsDetects']
        if len(testDetects_list) == 0:
                testDetects = "Unspecified"
        else:
                testDetects = testDetects_list[0]['Name']
        print(cancer_type)
        if cancer_type != disease:
                print("Subtype: "+disease)
        Tests = biomarker['Tests'][0]['Name']
        print(Tests)
        print("Test Detects: "+testDetects)
        MolecularAbnormalities = biomarker['MolecularAbnormalities'][0]['Name']
        if MolecularAbnormalities != Tests:
                print("Molecular Abnormalities: "+MolecularAbnormalities)
        if (len(biomarker['Chromosomes']) == len(biomarker['GeneSymbols'])) & (len(biomarker['Chromosomes']) > 0):
                for locus in range(0, len(biomarker['Chromosomes'])):
                        print(biomarker['Chromosomes'][locus]['Name']+" "+biomarker['GeneSymbols'][locus]['Name'])        
        else:
                if len(biomarker['Chromosomes']) > 0:
                        for locus in range(0, len(biomarker['Chromosomes'])):
                                print(biomarker['Chromosomes'][locus]['Name'])
                else:
                        print("No Associated Chromosomes")
                if len(biomarker['GeneSymbols']) > 0:
                        for locus in range(0, len(biomarker['GeneSymbols'])):
                                print(biomarker['GeneSymbols'][locus]['Name'])
                else:
                        print("No Associated Genes")

def cleanhtml(raw_html):
        cleantext = re.sub(CLEANR, '', raw_html)
        return cleantext

parser = argparse.ArgumentParser(description='NCCN biomarker compendium parser')
parser.add_argument('-t', '--cancer_type')
parser.add_argument('-j', '--compendium')
args = parser.parse_args()
cancer_type = args.cancer_type

guidelines = retrieve_NCCN_json(cancer_type, input_file_location=args.compendium)
pull_out_key_attributes(guidelines, cancer_type)
