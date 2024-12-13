**************************************************************************************************
  
# GENERATING ICD LOOKUP TABLE

Date: December 2024

Author: Ethan Ward

This readme describes the process to generate icd code lookup tables and a conversion table
from ICD-9 to ICD-10 classification. Despite extensive documentation regarding the icd codes, there seem to be no official
tabulated versions of the codes and their categorisation, nor a particularly good resource for converting
across the old system to the new one. I upload my versions of these tables, which I created for the sake of analysing
electronic health records, in case anyone carrying out similar research finds them or the code that created them useful.
This repository then includes:

- A tabulated version of both ICD-9 and ICD-10 codes, where each code is associated
	with a corresponding category (e.g. 'Neoplasms') and subcategory (e.g. 'Malignant
	Neoplasms of Lip, Oral Cavity and Pharynx'). Done for all codes ('full') and only
	integer codes (e.g. 001) ('part').

- A conversion table where old ICD-9 codes are matched to a
	corresponding ICD-10 code and category/subcategory. The need for a conversion
	table is due to the fact that ICD-9 and ICD-10 categorisation are different.
	So, to compare how, for instance, prevalence of conditions of a certain category develops
	over time, conversion is needed from ICD-9 codes to ICD-10 categorisation, or vice versa.



## DICTIONARY OF FILES

Raw Data

- \icd9\raw_pdfs\additional-diag-codes.pdf (\diag-codes_*.pdf; \v01_supplementary.pdf): 	
	  raw ICD-9 codebooks.
  
- \icd10\raw_pdfs\icd10cm-tabular-April 1 2023.pdf: raw ICD-10 codebook.

Processed Raw Data

- \icdcategorization.csv: category equivalence table created manually. 

- \icd9\icd9_rawtext.txt: icd-9 codebooks converted to raw text.

- \icd10\icd10_subcategories_valid.txt: list of valid icd-10 subcategories.

- \icd10\icd10_rawtext.txt: icd-10 codebook converted to raw text.

Scripts
	
- \icd9\parseicd9_full.py (\parseicd9_part.py): script to parse icd-9 raw text into lookup table.

- \icd10\parseicd10_full.py (\parseicd10_part.py): script to parse icd10 raw text into lookup table. 

- \icd9\icd9-equivalence-mapping.py: script to categorise icd-9 codes in icd-10 classification (fuzzy matching).

- \merging_fuzzy_manual.R: script to merge fuzzy and manually matched icd-9 codes into single categorisation table.

Intermediate Data

- \icd9_icd10_part_equivalence_manual.csv: table of manually categorised icd-9 codes.

- \icd9_icd10_part_subcategory_equivalence_fuzzymatched.csv: table of fuzzy matching categorised icd-9 codes.
	
Output Tables

- \icd9\parseicd9_full.csv (\parseicd9_part.csv): ICD-9 LOOKUP TABLE.

- \icd10\parseicd10_full.csv (\parseicd10_part.csv): ICD-10 LOOKUP TABLE.

- \icd9_icd10_part_subcategory_equivalence_merged.csv: ICD-9 -> ICD-10 CLASSIFICATION.


## USAGE DETAILS

Raw inputs: the sources for this table are the best structured documentation for ICD codes I
could find. The ICD-9 codes come from the government of British Columbia's website with
resources for practitioners, which I found to be a particularly clean and well organised
codebook, compared to some of the others available from reliable sources:

https://www2.gov.bc.ca/gov/content/health/practitioner-professional-resources/msp/physicians/diagnostic-code-descriptions-icd-9 

The ICD-10 codes come from the Centers for Disease Control and Prevention's website, which
again I found to be the cleanest codebook available: 

https://www.cdc.gov/nchs/icd/icd-10-cm/index.html

Overview of methods: to convert these into a workable dataset, I: convert the pdfs into raw text; 
use a regex program to parse this text into a list of codes, with corresponding categories,
subcategories; define a common categorisation of at least the highest level 'category',
e.g. 'Neoplasms', so that the codes are somewhat comparable; convert ICD-9 codes to corresponding
ICD-10 codes, with ICD-10 categorisation. 

Step 1: pdfs -> raw text

This is a fairly straightforward copy paste, but I did have to manually check that each 
	code takes up a single line only, which is key to enabling the parser to work properly. 
	In a few instances, I had to correct the text where a line had spilled over onto two rows.
	This is problematic as the parser does not identify a number on  the second row, and treats
	it as a new category header. Also problematic is the block of text after each 'chapter' in
	the ICD-10 codes, and I cut these out of the text. 

- Inputs: icd9/raw_pdfs/diag-codes*; icd9/raw_pdfs/v01_supplementary; icd9/rawpdfs/additional-diag-codes; icd10/raw_pdfs/icd10cm-tabular-April 1 2023.

- Outputs: icd9/icd9_rawtext.txt; icd10/icd10_rawtext.txt

Step 2: raw text -> icd9, icd10 lookup tables (first output)

I use a regex program in python here to parse the text into a workable .csv dataset. 
	I create two versions: one where each code is categorised 
	(parseicd9_full.csv/parseicd10_full.csv), and one where only integer codes are classified
	(parseicd9_part.csv/parseicd10_part.csv). I convert all strings to lowercase, to make
	comparison and merging easier down the line. 

- Inputs: icd9/icd9_rawtext.txt; icd10/icd10_rawtext.txt

- Code: icd9/parseicd9_full.py; icd9/parseicd9_part.py; icd10/parse_icd10_full.py;icd10/parse_icd10_full.py.

- Output: icd9/parseicd9_full.csv; icd9/parseicd9_part.csv; icd10/parse_icd10_full.csv; icd10/parse_icd10_full.csv.

Step 3: adding common categorisation, conversion.

The conversion of common categorisation at the 'category' level is fairly 
	straightforward as the names do not change very much from ICD-9 and ICD-10. I then
	use fuzzy matching to try to match integer ICD-9 codes to their ICD-10 equivalent
	based on description. These matches are then verified by ensuring they have a common
	'commoncat' i.e. the same 'category'. 

Codes are first matched using their subcategory.
	There are many cases where the same or very similar subcategory names are being used
	in ICD-9 as in ICD-10. I use fuzzy matching to find these cases and classify such codes
	(~50%). Then, code 'descriptions' are often similar in both, so the remaining unmatched codes
	are fuzzy matched on description (~30%). The remaining codes which cannot be fuzzy matched on either subcategory or description
	are manually converted (~20%). 

- Inputs: icd9/parseicd9_part.csv; icd10/parseicd10_part.csv.

- Code: icd9/icd9-equivalence-mapping.py; merging_fuzzy_manual.R

- Intermediate: icd9_icd10_part_equivalence_manual.csv; icd9_icd10_part_subcategory_equivalence_fuzzymatched.csv.

- Output: icd9_icd10_part_subcategory_equivalence_merged.csv


**************************************************************************************************
