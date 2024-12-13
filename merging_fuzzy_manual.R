################################################################################
#                                                                              #
#             MERGING FUZZY AND MANUAL CODE EQUIVALENCE INTO                   #
#                   SINGLE ICD9 -> ICD10 CATEGORISATION                        #
#                                                                              #
# Date:     December 2024                                                      #
# Author:   Ethan Ward                                                         #
#                                                                              #
# Purpose:  This script merges the two parts of the ICD-9 -> ICD-10            #
#           conversion: i.e. manual conversions + fuzzymatched -> single       #
#           conversion table. Note that ICD-9 codes are only 'converted' to    #
#           ICD-10 in the sense that they are classified as their equivalent   #
#           in ICD-10 would be. I do not create a 1-to-1 match between ICD-9   #
#           codes and ICD-10.                                                  #
#                                                                              #
# Inputs:  - Fuzzy matched ICD-9 codes (icd9...fuzzymatched.csv)               #
#          - Manually matched ICD-9 codes (icd9...manual.csv)                  #
#                                                                              #
# Outputs: - Merged conversion table (icd9...merged.csv)                       #
#                                                                              #
################################################################################

# Load packages
library(readxl)
library(dplyr)

# Load tables
fuzzy <- read.csv("C:/Users/ethan/Dropbox/Gender Without Kids/Data/ICDcodes/icd9_icd10_part_subcategory_equivalence_fuzzymatched.csv")
manual <- read.csv("C:/Users/ethan/Dropbox/Gender Without Kids/Data/ICDcodes/icd9_icd10_part_equivalence_manual.csv")

# Prepare tables for merge
manual <- manual %>%
  select(code,
         manual_icd10,
         subcategory_icd10)

fuzzy <- fuzzy %>%
  select(code,
         description,
         subcategory,
         commoncat,
         icd10subcategory,
         MatchStage)

# Merging
merged_conversion <- merge(fuzzy, manual, by.x = "code", by.y = "code", all.x = TRUE)

# Cleaning merged table: creating single icd10 subcategory variable; match stage variable
merged_conversion <- merged_conversion %>%
  mutate(icd10subcategory = ifelse(!is.na(manual_icd10), subcategory_icd10, icd10subcategory)
         )

merged_conversion <- merged_conversion %>%
  select(-subcategory_icd10)

merged_conversion <- merged_conversion %>%
  mutate(icd10subcategory = ifelse(icd10subcategory == "", "no conversion", icd10subcategory))

merged_conversion <- merged_conversion %>%
  mutate(MatchStage = ifelse(!is.na(manual_icd10) & manual_icd10 != "no conversion", "manual by code", MatchStage)) %>%
  mutate(MatchStage = ifelse(MatchStage == "manual", "manual by category", MatchStage)) %>%
  mutate(MatchStage = ifelse(MatchStage == "skipped_subcategory", "fuzzy by code", MatchStage)) %>%
  mutate(MatchStage = ifelse(icd10subcategory == "no conversion", NA, MatchStage)) %>%
  mutate(MatchStage = ifelse(MatchStage == "subcategory", "fuzzy by subcategory", MatchStage))

# Saving as new csv
write.csv(merged_conversion, "C:/Users/ethan/Dropbox/Gender Without Kids/Data/ICDcodes/icd9_icd10_part_subcategory_equivalence_merged.csv", row.names = FALSE)

