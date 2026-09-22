# Chest-condition annotation and QC guidelines

## Scope

The supplied `Ground_Truth.csv` is CSV-based and contains image-level
`Finding Labels`.

It is not a folder-label file and does not provide bounding boxes or
lesion masks.

The code also supports folder-based labels.

For folder labels:

label_source: folder

and use:

raw/images/<condition>/<image file>

## Connection rule

Use `Image Index` to recursively match each metadata record to a
local image filename.

Duplicate local filenames are flagged as ambiguous instead of being
guessed.

## Label rule

Split multi-label strings on `|`.

Retain source spelling.

Flag:

- empty labels
- unknown labels
- No Finding conflicts

## Metadata rule

Validate:

- missing files
- orphan images
- duplicate image identifiers
- age
- gender
- view position
- label spelling

## Image QC rule

Automated checks cover:

- corruption
- blankness
- blur
- contrast
- pixel clipping
- exact duplicates
- near-duplicate candidates

Thresholds are configurable in:

configs/chest_condition.yaml

## Review rule

Records needing further investigation are exported for external review.

Reviewer decisions are written to:

The primary reporting outputs are the Power BI-ready CSV files under
`powerbi/chest_condition/`.