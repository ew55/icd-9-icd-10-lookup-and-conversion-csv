#########################################################################################################
#                                  PARSING ICD-9 RAW TEXT INTO LOOKUP TABLE                             #
#                                                                                                       #
#   Date:    December 2024                                                                              #
#   Author:  Ethan Ward                                                                                 #
#                                                                                                       #
#   Purpose: This script parses the raw text form of the tabulated ICD-9 codes (from pdfs) into a       #
#            workable lookup table, i.e. where each code has a description/definition, subcategory and  #
#            category (three ascending hierarchical classifications of ICD codes). This is the 'part'   #
#            version, which only is concerned with the integer codes, i.e. 999 not 999.1.               #
#                                                                                                       #
#   Inputs:  - Raw text icd-9 codebook (icd9_rawtext.txt)                                               #
#            - Common category categorization table (icdcategorisation.xlsx) [to add common icd-9 and   #
#              icd-10 category as a column].                                                            #  
#                                                                                                       #
#   Outputs: - ICD-9 'part' lookup table (parseicd9_part.csv)                                           #
#                                                                                                       #   
#   Contents: 1. Defining parsing program:                                                              #
#                   regex to identify code;                                                             #
#                   regex to identify subcat;                                                           #
#                   regex to identify cat;                                                              #
#                   small cleaning/duplicates dropping where parsed erroneously                         #
#             2. Define merge with categorization table to add commoncat                                #
#             3. Loading tables.                                                                        #
#             4. Execute & Save                                                                         #
#                                                                                                       #
#########################################################################################################

# Loading packages
import pandas as pd
import re
import openpyxl
import numpy as np

## Defining parsing program ##
# This is a regex program which aims to extract each code, subcategory header and category header.
# There are clear patterns to which lines are which for the above, and the regex looks for these.
def parse_text_to_csv(input_file_path, output_file_path, categorization_path):
    with open(input_file_path, 'r', encoding='utf-8') as file:
        lines = file.readlines()

    data = []
    current_category = None
    current_subcategory = None
    flags = {
        'categories_without_subcategories': [],
        'codes_with_inserted_decimal': []
    }

    # Skipping empty lines
    for idx, line in enumerate(lines):
        line = line.strip()
        if not line:
            continue 
        
        # Checking if the line is a code
        # Regex for 'code' lines - looks for pattern such as 123 or V01
        code_match = re.match(r'^([0-9]+|[VE][0-9]+|[0-9]{2}[A-Z])(\.\d+)?\s+(.*)', line)
        if code_match:
            code = code_match.group(1)
            decimal_part = code_match.group(2) if code_match.group(2) else ''
            description = code_match.group(3)

            # Skiping codes that have a decimal (as this is the 'part' not 'full' lookup table)
            if decimal_part:
                continue

            # Converting all to lowercase
            code = code.lower()
            description = description.lower()

            # Veerifying code: must be exactly three characters long
            if len(code) != 3:
                continue

            category = current_category.lower() if current_category else ''
            subcategory = current_subcategory.lower() if current_subcategory else ''

            data.append({
                'code': code,
                'description': description,
                'category': category,
                'subcategory': subcategory
            })
            continue

        # Checking if the line is a subcategory
        subcategory_match = re.match(
            r'^(.*?)\s+\(([VE]?\d+(\.\d+)?\s*[-–]\s*[VE]?\d+(\.\d+)?)\)$', line)
        if subcategory_match:
            current_subcategory = subcategory_match.group(1).strip().lower()
            continue

        # EXCEPTION 
        # For 'ADDITIONAL DIAGNOSTIC CODES'
        if line.strip().upper() == 'ADDITIONAL DIAGNOSTIC CODES':
            current_category = 'ADDITIONAL DIAGNOSTIC CODES'
            current_subcategory = 'ADDITIONAL DIAGNOSTIC CODES'
            continue

        # EXCEPTION
        # Treat 'SUPPLEMENTARY CLASSIFICATION OF FACTORS INFLUENCING HEATLH STATUS AND CONTACT WITH HEALTH SERVICES'
        # as a category line.
        if line.strip().upper() == 'SUPPLEMENTARY CLASSIFICATION OF FACTORS INFLUENCING HEATLH STATUS AND CONTACT WITH HEALTH SERVICES':
            current_category = 'SUPPLEMENTARY CLASSIFICATION OF FACTORS INFLUENCING HEATLH STATUS AND CONTACT WITH HEALTH SERVICES'
            current_subcategory = 'PERSONS WITH HEALTH HAZARDS RELATED TO COMMUNICABLE DISEASES (V01 – V07.9)'
            continue

        # Checking if the line is a category
        # We double check that the category is followed by a new sub-category to verify. 
        if idx + 1 < len(lines):
            next_line = lines[idx + 1].strip()
            next_is_subcategory = re.match(
                r'^(.*?)\s+\(([VE]?\d+(\.\d+)?\s*[-–]\s*[VE]?\d+(\.\d+)?)\)$', next_line)
            if next_is_subcategory:
                current_category = line.strip().lower()
                current_subcategory = None 
            else:
                flags['categories_without_subcategories'].append(line.strip())
            continue

    # Create df
    df = pd.DataFrame(data, dtype=str)

    # Merge with the categorization excel to add commoncat column.
    df_cat = pd.read_excel(categorization_path, dtype=str)

    # Ensure icd9cat and commoncat are lowercase in categorization excel
    df_cat['icd9cat'] = df_cat['icd9cat'].str.lower()
    df_cat['commoncat'] = df_cat['commoncat'].str.lower()

    # Merge on category (in df) and icd9cat (in df_cat)
    df_merged = df.merge(df_cat[['icd9cat', 'commoncat']], left_on='category', right_on='icd9cat', how='left')

    # Drop the icd9cat column as not needed
    df_merged.drop(columns=['icd9cat'], inplace=True)

    # Dropping pure duplicates
    df_merged = df_merged.drop_duplicates(subset=['code'], keep='first')

    # Save the merged df to csv
    df_merged.to_csv(output_file_path, index=False)

    # Print flags
    if flags['categories_without_subcategories']:
        print("Categories without subcategories (ignored):")
        for category in flags['categories_without_subcategories']:
            print(f"- {category}")

    if flags['codes_with_inserted_decimal']:
        print("\nCodes where decimal point was inserted:")
        for code in flags['codes_with_inserted_decimal']:
            print(f"- {code}")

# Paths
input_file_path = 'C:/Users/ethan/Dropbox/Gender Without Kids/Data/ICDcodes/icd9/icd9_rawtext.txt'
output_file_path = 'C:/Users/ethan/Dropbox/Gender Without Kids/Data/ICDcodes/icd9/parseicd9_part.csv'
categorization_path = 'C:/Users/ethan/Dropbox/Gender Without Kids/Data/ICDcodes/icdcategorisation.xlsx'

# Execute
parse_text_to_csv(input_file_path, output_file_path, categorization_path)
