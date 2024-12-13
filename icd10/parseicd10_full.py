#########################################################################################################
#                                  PARSING ICD-10 RAW TEXT INTO LOOKUP TABLE                            #
#                                                                                                       #
#   Date:    December 2024                                                                              #
#   Author:  Ethan Ward                                                                                 #
#                                                                                                       #
#   Purpose: This script parses the raw text form of the tabulated ICD-10 codes (from pdfs) into a      #
#            workable lookup table, i.e. where each code has a description/definition, subcategory and  #
#            category (three ascending hierarchical classifications of ICD codes). This is the 'full'   #
#            version, which is concerned with all codes, i.e. including non-integer codes like A01.1    #
#                                                                                                       #
#   Inputs:  - Raw text icd-10 codebook (icd10_rawtext.txt)                                             #
#            - 'Valid subcategories' text file (icd10_subcategories_valid.txt) [to verify               #
#               subcategories]                                                                          #
#            - Common category categorization table (icdcategorisation.xlsx) [to add common icd-9 and   #
#              icd-10 category as a column].                                                            #  
#                                                                                                       #
#   Outputs: - ICD-10 'full' lookup table (parseicd10_full.csv)                                         #
#                                                                                                       #   
#   Contents: 1. Defining subcat verification program                                                   #
#             2. Defining parsing program:                                                              #
#                   regex to identify code;                                                             #
#                   regex to identify subcat;                                                           #
#                   regex to identify cat                                                               #
#             2. Defining merge with categorization table to add commoncat                              #
#             3. Loading tables.                                                                        #
#             4. Execute & Save                                                                         #
#                                                                                                       #
#########################################################################################################

# Loading packages
import pandas as pd
import re

## Defining subcategory validation using only subcategories which are in icd10_subcategories_valid.txt
def load_valid_subcategories(file_path):
    """ Load valid subcategories from a given file path """
    with open(file_path, 'r', encoding='utf-8') as file:
        return [line.strip() for line in file.readlines()]

def is_valid_subcategory(name, valid_subcategories):
    """ Check if the subcategory name appears within any of the valid subcategories """
    for valid_name in valid_subcategories:
        if name in valid_name:
            return True
    return False

## Defining parsing program ##
# This is a regex program which aims to extract each code, subcategory header and category header.
# There are clear patterns to which lines are which for the above, and the regex looks for these.
def parse_text_to_csv(input_file_path, output_file_path, subcategory_file_path):
    valid_subcategories = load_valid_subcategories(subcategory_file_path)

    with open(input_file_path, 'r', encoding='utf-8') as file:
        lines = file.readlines()

    data = []
    current_category = None
    current_subcategory = None
    subcategory_active = False

    for i, line in enumerate(lines):
        line = line.strip()
        # Checking if category
        if re.match(r'Chapter \d+\s*$', line):
            current_category = lines[i + 1].strip().lower()
            i += 1

        # Checking if subcategory
        elif match := re.match(r'^([A-Z][\w\s,\[\]-]*?)( \(([A-Z]\d[A-Z0-9]?)(-[A-Z]\d[A-Z0-9]?)?\))$', line):
            subcategory_name = match.group(1)
            if is_valid_subcategory(subcategory_name, valid_subcategories):
                current_subcategory = subcategory_name.lower()
                subcategory_active = True
            else:
                print(f"Invalid or unrecognized subcategory: {subcategory_name}")

        # Checking if code (when subcategory is active)
        elif subcategory_active and (match := re.match(r'^([A-Z]\d[A-Z0-9]?(\.\d+)?([A-Z]?)?)\s+(.*)', line)):
            code = match.group(1).lower()           
            full_description = match.group(4).lower() 
            data.append({
                'code': code,
                'description': full_description,
                'subcategory': current_subcategory,
                'category': current_category
            })
        else:
            # Flag 'codes' which appear outside active subcats
            if not subcategory_active and line:
                print(f"Non-matching line outside subcategories: {line}")

    # Create df
    df = pd.DataFrame(data, dtype=str)

    # Merging with the categorisation Excel file to get 'commoncat'
    categorization_path = 'C:\\Users\\ethan\\Dropbox\\Gender Without Kids\\Data\\ICDcodes\\icdcategorisation.xlsx'
    df_cat = pd.read_excel(categorization_path, dtype=str)

    # To lowercase
    df_cat['icd10cat'] = df_cat['icd10cat'].str.lower()
    df_cat['commoncat'] = df_cat['commoncat'].str.lower()

    # Ensuring df['category'] is lowercase (it already should be)
    df['category'] = df['category'].str.lower()

    # Merging on category (from df) and icd10cat (from df_cat) to get commoncat column
    df_merged = df.merge(df_cat[['icd10cat', 'commoncat']],
                          left_on='category',
                          right_on='icd10cat',
                          how='left')

    # Drop the icd10cat column as not needed
    df_merged.drop(columns=['icd10cat'], inplace=True)

    # Save the merged df to CSV
    df_merged.to_csv(output_file_path, index=False)

    print("Parsing and merging completed. The new file with commoncat column is saved.")

# Paths
processed_file_path = 'C:\\Users\\ethan\\Dropbox\\Gender Without Kids\\Data\\ICDcodes\\icd10\\icd10_rawtext.txt'
csv_output_file_path = 'C:\\Users\\ethan\\Dropbox\\Gender Without Kids\\Data\\ICDcodes\\icd10\\parseicd10_full.csv'
subcategory_file_path = 'C:\\Users\\ethan\\Dropbox\\Gender Without Kids\\Data\\ICDcodes\\icd10\\icd10_subcategories_valid.txt'

# Executing
parse_text_to_csv(processed_file_path, csv_output_file_path, subcategory_file_path)
