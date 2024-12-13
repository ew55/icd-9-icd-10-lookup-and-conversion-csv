#########################################################################################################
#                                  PARSING ICD-9 RAW TEXT INTO LOOKUP TABLE                             #
#                                                                                                       #
#   Date:    December 2024                                                                              #
#   Author:  Ethan Ward                                                                                 #
#                                                                                                       #
#   Purpose: This script parses the raw text form of the tabulated ICD-9 codes (from pdfs) into a       #
#            workable lookup table, i.e. where each code has a description/definition, subcategory and  #
#            category (three ascending hierarchical classifications of ICD codes). This is the 'full'   #
#            version, which includes all codes not just integers i.e. including 999.1.                  #
#                                                                                                       #
#   Inputs:  - Raw text icd-9 codebook (icd9_rawtext.txt)                                               #
#            - Common category categorization table (icdcategorisation.xlsx) [to add common icd-9 and   #
#              category as a column].                                                                   #  
#                                                                                                       #
#   Outputs: - ICD-9 'full' lookup table (parseicd9_full.csv)                                           #
#                                                                                                       #   
#   Contents: 1. Defining parsing program:                                                              #
#                   regex to identify code;                                                             #
#                   regex to identify subcat;                                                           #
#                   regex to identify cat;                                                              #
#                   small cleaning/duplicates dropping where parsed erroneously                         #
#             2. Defining merge with categorization table to add commoncat                              #
#             3. Loading tables.                                                                        #
#             4. Execute & Save                                                                         #
#                                                                                                       #
#########################################################################################################

import pandas as pd
import re
import openpyxl

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


    for idx, line in enumerate(lines):
        line = line.strip()
        if not line:
            continue  # Skip empty lines


        # Updated code regex to allow codes like "00A"
        code_match = re.match(r'^([0-9]+|[VE][0-9]+|[0-9]{2}[A-Z])(\.\d+)?\s+(.*)', line)
        if code_match:
            code = code_match.group(1)
            decimal_part = code_match.group(2) if code_match.group(2) else ''
            description = code_match.group(3)


            # Insert decimal point if code has four digits and no decimal
            if not decimal_part and len(code) == 4 and code[0].isdigit():
                code = f"{code[:3]}.{code[3]}"
                flags['codes_with_inserted_decimal'].append(code)
            else:
                code = code + decimal_part


            # Convert to lowercase
            code = code.lower()
            description = description.lower()
            category = current_category.lower() if current_category else ''
            subcategory = current_subcategory.lower() if current_subcategory else ''


            data.append({
                'code': code,
                'description': description,
                'category': category,
                'subcategory': subcategory
            })
            continue


        # Check if the line is a subcategory
        subcategory_match = re.match(
            r'^(.*?)\s+\(([VE]?\d+(\.\d+)?\s*[-–]\s*[VE]?\d+(\.\d+)?)\)$', line)
        if subcategory_match:
            current_subcategory = subcategory_match.group(1).strip().lower()
            continue


        # Exception for 'ADDITIONAL DIAGNOSTIC CODES'
        if line.strip().upper() == 'ADDITIONAL DIAGNOSTIC CODES':
            current_category = 'ADDITIONAL DIAGNOSTIC CODES'
            current_subcategory = 'ADDITIONAL DIAGNOSTIC CODES'
            continue


        # **New Exception:**
        # Treat 'supplementary classification of factors influencing health status and contact with health services (v01-v82)' as a category line
        if line.strip().upper() == 'SUPPLEMENTARY CLASSIFICATION OF FACTORS INFLUENCING HEATLH STATUS AND CONTACT WITH HEALTH SERVICES':
            current_category = 'SUPPLEMENTARY CLASSIFICATION OF FACTORS INFLUENCING HEATLH STATUS AND CONTACT WITH HEALTH SERVICES'
            current_subcategory = 'PERSONS WITH HEALTH HAZARDS RELATED TO COMMUNICABLE DISEASES (V01 – V07.9)'
            continue


        # Check if the line is a category
        if idx + 1 < len(lines):
            next_line = lines[idx + 1].strip()
            next_is_subcategory = re.match(
                r'^(.*?)\s+\(([VE]?\d+(\.\d+)?\s*[-–]\s*[VE]?\d+(\.\d+)?)\)$', next_line)
            if next_is_subcategory:
                current_category = line.strip().lower()
                current_subcategory = None  # Reset subcategory when a new category is found
            else:
                # Next line is not a subcategory, so ignore this category (unless it's an exception)
                flags['categories_without_subcategories'].append(line.strip())
            continue


    # Create DataFrame with 'code' as string type
    df = pd.DataFrame(data, dtype=str)


    # Before saving, merge with the categorization Excel file
    df_cat = pd.read_excel(categorization_path, dtype=str)


    # Ensure icd9cat and commoncat are lowercase
    df_cat['icd9cat'] = df_cat['icd9cat'].str.lower()
    df_cat['commoncat'] = df_cat['commoncat'].str.lower()


    # Merge on category (in df) and icd9cat (in df_cat)
    df_merged = df.merge(df_cat[['icd9cat', 'commoncat']], left_on='category', right_on='icd9cat', how='left')


    # Drop the icd9cat column if not needed
    df_merged.drop(columns=['icd9cat'], inplace=True)


    # Save the merged DataFrame to CSV
    df_merged.to_csv(output_file_path, index=False)


    # Print flag messages
    if flags['categories_without_subcategories']:
        print("Categories without subcategories (ignored):")
        for category in flags['categories_without_subcategories']:
            print(f"- {category}")


    if flags['codes_with_inserted_decimal']:
        print("\nCodes where decimal point was inserted:")
        for code in flags['codes_with_inserted_decimal']:
            print(f"- {code}")


# Specify your file paths
input_file_path = 'C:/Users/ethan/Dropbox/Gender Without Kids/Data/ICDcodes/icd9/icd9_rawtext.txt'
output_file_path = 'C:/Users/ethan/Dropbox/Gender Without Kids/Data/ICDcodes/icd9/parseicd9_full.csv'
categorization_path = 'C:/Users/ethan/Dropbox/Gender Without Kids/Data/ICDcodes/icdcategorisation.xlsx'

# Parse the text file into a CSV and merge with common categories
parse_text_to_csv(input_file_path, output_file_path, categorization_path)
