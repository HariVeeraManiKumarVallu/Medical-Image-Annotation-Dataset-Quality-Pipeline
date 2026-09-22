# Power BI Dashboard Guide

The pipeline exports Power BI-ready CSV files under `powerbi/<dataset>/`.

## Import and refresh

1. Open Power BI Desktop.
2. Select **Get data** and choose **Text/CSV**.
3. Import the files for one dataset:
   - `cleaned_manifest.csv`
   - `quality_summary.csv`
   - `validation_issues.csv`
   - `duplicates.csv`
   - `rejected_records.csv` (reserved for future external review imports)
   - `label_counts.csv`
   - `before_after.csv`
   - `schema_drift.csv`
4. Set `image_id` and `Patient ID` as text where leading zeroes must be preserved.
5. Use `quality_summary.csv` for KPI cards.

The Excel workbook is intentionally a compact summary. Use the Power BI CSV
tables for full record-level detail.

Save the report as a `.pbix` file in Power BI Desktop. On later runs, replace
or refresh the CSV files in the same `powerbi/<dataset>/` folder and select
**Refresh** in Power BI. Do not import the generated HTML reports; HTML
reporting has been removed from this project.

## Recommended report pages

### Overview

- Total records
- Matched records
- Missing records
- PASS, REVIEW, REJECT, and UNAVAILABLE counts
- Average quality score
- Validation issue count
- Duplicate candidate count

### Image quality

Use `cleaned_manifest.csv` for:

- Quality-score distribution
- Blur and contrast distributions
- Pixel entropy and noise
- Clipping and background ratios
- Quality flags by count

### Metadata quality

Use `validation_issues.csv` and `schema_drift.csv` for:

- Errors by reason code
- Missing-image counts
- Invalid age, gender, view, and label values
- Source-versus-processed columns and data types

### Labels and patients

Use `label_counts.csv` for label frequency charts. Use the generated ML output
`patient_groups.csv` for patient-level image counts.

### Duplicate and review analysis

Use `duplicates.csv` for:

- Exact and near-duplicate counts
- Rejected records

## Important interpretation rules

- `PASS` means automated checks found no configured issue.
- `REVIEW` means the record needs further investigation outside this automated pipeline.
- `UNAVAILABLE` means metadata exists but the image is not in the local subset.
- Anomaly scores are prioritization signals, not diagnoses.
- Power BI presents dataset quality results; it does not establish clinical truth.
