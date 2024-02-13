(mdc_formats)=
# MDC formats

This document contains current and previous MDC formats for reference.

### Version 2.0: 2023-02-13

The following elements _must_ appear in this order:
1. A section with exactly 11 entries of the form `key = value`
2. A separator consisting of 3 hash marks: `###`
3. Summary text

The 11 entries correspond to the 8 PHI fields listed above:
1. `patient_name`
2. `patient_dob`
3. `patient_genetic_sex`
4. `requisitioner_email`
5. `physician_licence_number`
6. `physician_name`
7. `physician_phone_number`
8. `hospital_name_and_address`
9. `report_signoff_date`
10. `clinical_geneticist_name`
11. `clinical_geneticist_licence`

These entries may occur in any order, but _must_ be present and have non-empty values.

Field 9 is filled in with the current date but can be changed by the user.

Summary text must be non-empty. Leading or trailing whitespace will be removed before the text is inserted into the report; but whitespace, including line breaks, may occur within the text block. Formatting with [Markdown notation](https://www.markdownguide.org/cheat-sheet/) and/or HTML tags is supported. This enables the user to create or edit bold/italic text, hyperlinks, etc.

### Version 1.0: 2023-01-31

The following elements _must_ appear in this order:
1. A section with exactly 8 entries of the form `key = value`
2. A separator consisting of 3 hash marks: `###`
3. Summary text

The 8 entries correspond to the 8 PHI fields listed above:
1. `patient_name`
2. `patient_dob`
3. `patient_genetic_sex`
4. `requisitioner_email`
5. `physician_licence_number`
6. `physician_name`
7. `physician_phone_number`
8. `hospital_name_and_address`

These entries may occur in any order, but _must_ be present and have non-empty values.

Summary text must be non-empty. Leading or trailing whitespace will be removed before the text is inserted into the report; but whitespace, including line breaks, may occur within the text block. Formatting with [Markdown notation](https://www.markdownguide.org/cheat-sheet/) and/or HTML tags is supported. This enables the user to create or edit bold/italic text, hyperlinks, etc.
