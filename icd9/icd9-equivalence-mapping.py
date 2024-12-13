##########################################################################################################################################
#                                                  ICD-9 -> ICD-10 CLASSFICIATION                                                        #
#                                                                                                                                        #
#  Date:      December 2024                                                                                                              #
#  Author:    Ethan Ward                                                                                                                 #
#                                                                                                                                        #
#  Purpose:   This script completes the first part of the conversion of the old ICD-9 codes into their corresponding ICD-10              #
#             'subcategories'. The second part is done manually, and the two tables are merged in another script                         #
#             (merging_fuzzy_manual.R) The aim of this is to enable comparison across ICD-9 and ICD-10 codes at a level less granular    #
#             than the codes themselves, for instance using EHRs.                                                                        #
#                                                                                                                                        #
#  Inputs:    - Parsed ICD-9 lookup table: parseicd9_part.csv                                                                            #
#             - Parsed ICD-10 lookup table: parseicd10_part.csv                                                                          #
#                                                                                                                                        #
#  Outputs:   - icd9_icd10_part_subcategory_equivalence_fuzzymatched.csv                                                                 #
#                                                                                                                                        #
#  Contents:  1. Loading and preparing parsed lookup tables.                                                                             #
#             2. Define dictionary of problematic subcategories which need to be skipped.                                                #
#             3. Iterative fuzzy matching: first on subcategory, keeping only matches with same category, and which are a correct match  #
#             (verified manually).                                                                                                       #
#             4. Saving                                                                                                                  #
#                                                                                                                                        #
##########################################################################################################################################

# Loading packages
import pandas as pd
from rapidfuzz import process, fuzz
import string

# Loading ICD-9 and ICD-10 lookup tables
table_a = pd.read_csv('C:/Users/ethan/Dropbox/Gender Without Kids/Data/ICDcodes/icd9/parseicd9_part.csv', dtype=str)
table_b = pd.read_csv('C:/Users/ethan/Dropbox/Gender Without Kids/Data/ICDcodes/icd10/parseicd10_part.csv', dtype=str)

## Preparing the data ##
# All cols to strings
table_a = table_a.astype(str)
table_b = table_b.astype(str)

# All cols to lowercase
for col in ['subcategory', 'description', 'commoncat', 'code']:
    table_a[col] = table_a[col].str.lower()
    table_b[col] = table_b[col].str.lower()

# Cleaning descriptions
def clean_description(desc):
    return ' '.join(desc.lower().translate(str.maketrans('', '', string.punctuation)).split())

table_a['description_clean'] = table_a['description'].apply(clean_description)
table_b['description_clean'] = table_b['description'].apply(clean_description)

# Preparing dictionaries for matching
unique_b_subcategories = table_b['subcategory'].dropna().unique()
description_to_info_b = table_b.set_index('description_clean')[['code', 'subcategory', 'commoncat', 'description']].to_dict('index')
descriptions_b = table_b['description_clean'].dropna().unique()

# Problematic subcategories which need manual matching. 
# When fuzzy matched, these subcategories do not match into icd-10 subcategories well.
skip_subcategories = [
'poliomyelitis and other non-arthropod borne viral diseases of central nervous system',
'other diseases due to viruses and chlamydiae',
'rickettsiosis and other arthropod-borne diseases',
'syphilis and other venereal diseases',
'other infectious and parasitic diseases',
'malignant neoplasm of bone, connective tissue, skin and breast',
'malignant neoplasm of genitourinary organs',
'benign neoplasm',
'other metabolic disorders and immunity disorders',
'diseases of blood and blood forming organs',
'organic psychotic conditions',
'other psychoses',
'neurotic disorders, personality disorders and other nonpsychotic mental disorders',
'mental retardation',
'hereditary and degenerative diseases of central nervous system',
'disorders of the eye and adnexa',
'disorders of ear and mastoid process',
'diseases of veins and lymphatics, and other diseaseas of circulatory system',
'chronic obstructive pulmonary disease and allied conditions',
'other diseases of intestines and peritoneum',
'nephritis, nephrotic syndrome ans nephrosis',
'complications mainly related to pregnancy',
'normal delivery and other indications for care in pregnancy labour and delivery',
'other inflammatory conditions of skin and subcutaneous tissue',
'other diseases of skin and subcutaneous tissue',
'arthropathies and related disorders',
'rheumatism, excluding the back',
'osteopathies, chondropathies and ac quired musculoskeletal deformities',
'congenital anomalies',
'certain conditions originating in the perinatal period',
'symptoms',
'non-specific abnormal findings',
'fracture of upper limb',
'fracture of lower limb',
'dislocation',
'sprains and strains of joints and adjacent muscles',
'open wound of head, neck and trunk',
'open wounds of upper limb',
'open wounds of lower limb',
'injury to blood vessels',
'late effects of injuries, poisonings, toxic effects and other external causes',
'superficial injury',
'contusion with intact skin surface',
'crushing injury',
'injury to nerves and spinal cord',
'certain traumatic complications and unpspecified injuries',
'healthy liveborn infants according to type of birth',
'persons with conditions influencing their health status',
'persons without reported diagnosis encountered during examination and investigation of individals and populations',
'additional diagnostic codes'
]

## Defining the iterative matching procedure. This will take the following order: ##
    # Step 1: Manually match problematic icd-9 subcategories which have a clear partner in icd-10 classification. (~10%)
    # Step 2: Fuzzy matching on subcategory, i.e. each icd-9 code gets an icd-10 subcategory if its icd-9 subcategory has a 
    # good enough partner in icd-10. (~50%)
    # Step 3: Fuzzy matching on description, i.e. remaining icd-9 codes get matched to specific CODES in icd-10, and icd-10 subcategories
    # are taken from those. (~15%).
    # Step 4: Manual matching on description. The remaining codes which cannot be automatically matched on code or description are
    # manually assigned icd-10 subcategories, based on looking up equivalent icd-10 codes by hand. THIS STAGE IS NOT DONE IN THIS 
    # SCRIPT, BUT RATHER IN THE SEPERATE R SCRIPT merging_fuzzy_manual.R. 

def find_best_match(row):
    
    default_return = ('', '', '')

    # Skip problematic subcategories
    if row['subcategory'] in skip_subcategories:
        subcategory, description_used = match_by_description(row['description_clean'], row['commoncat'])
        return subcategory, 'skipped_subcategory', description_used if description_used else ''

    # Manual subcategories
    manual_matches = {
        "arthropod-borne viral diseases": ("Arthropod-borne viral fevers and viral haemorrhagic fevers"),
        "viral diseases accompanied by exanthem": ("Viral infections characterized by skin and mucous membrane lesions", "manual", ''),
        "carcinoma in situ": ("In situ neoplasms", "manual", ''),
        "neoplasms of unspecified nature": ("Neoplasms of unspecified behavior", "manual", ''),
        "appendicitis": ("Diseases of appendix", "manual", ''),
        "hernia of abdominal cavity": ("Hernia", "manual", ''),
        "ill-defined and unknown causes of morbidity and morality": ("Ill-defined and unknown cause of mortality", "manual", ''),
        "fracture of skull": ("Injuries to the head", "manual", ''),
        "fracture of spine and trunk": ("Injuries to the abdomen, lower back, lumber spine, pelvis and external genitals", "manual", ''),
        "intracranial injury excluding those with skull fractures": ("Injuries to the head", "manual", ''),
        "internal injury of chest, abdoment and pelvis": ("Injuries to the abdomen, lower back, lumber spine, pelvis and external genitals", "manual", '')
    }

    if row['subcategory'] in manual_matches:
        return manual_matches[row['subcategory']]

    # Fuzzy subcategory matching
    if row['subcategory']:
        subcat_match = process.extractOne(row['subcategory'], unique_b_subcategories, scorer=fuzz.token_set_ratio, score_cutoff=80)
        if subcat_match:
            matched_subcategory = subcat_match[0]
            entries = table_b[(table_b['subcategory'] == matched_subcategory) & (table_b['commoncat'] == row['commoncat'])]
            if not entries.empty:
                return matched_subcategory, 'subcategory', ''

    # Fuzzy description matching
    subcategory, description_used = match_by_description(row['description_clean'], row['commoncat'])
    return subcategory, 'description', description_used if description_used else ''

def match_by_description(description, commoncat):
    desc_match = process.extractOne(description, descriptions_b, scorer=fuzz.token_set_ratio, score_cutoff=50)
    if desc_match:
        matched_description = desc_match[0]
        match_info = description_to_info_b.get(matched_description)
        if match_info and match_info['commoncat'] == commoncat:
            return match_info['subcategory'], match_info['description']
    return '', ''

table_a[['icd10subcategory', 'MatchStage', 'MatchedBDescription']] = table_a.apply(lambda row: find_best_match(row), axis=1, result_type='expand')

## Results ##
total_codes = len(table_a)
matched_count = table_a['icd10subcategory'].apply(bool).sum()
unmatched_count = total_codes - matched_count

## Saving ##
table_a.to_csv('C:/Users/ethan/Dropbox/Gender Without Kids/Data/ICDcodes/icd9_icd10_part_subcategory_equivalence_fuzzymatched.csv', index=False)
print(f"Total codes in Table A: {total_codes}")
print(f"Number of codes matched by subcategory or description: {matched_count}")
print(f"Number of codes not matched at all: {unmatched_count}")