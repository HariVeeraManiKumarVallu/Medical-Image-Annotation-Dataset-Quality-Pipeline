# NIH sample annotation and QC guidelines

## Scope

This pipeline treats `sample_labels.csv` as the metadata/label source
and the image files as the actual visual records.

`Finding Labels` are image-level labels.

They are not bounding boxes or lesion masks.

## Connection rule

`Image Index` is matched to the local image filename after normalizing
the path to its filename stem.

Matching is recursive, so images can be stored in nested folders.

Example:

CSV:

00030712_000.png

Local image:

data/nih_sample/raw/images/00030712_000.png

Both normalize to:

00030712_000

## Label rule

Split `Finding Labels` on `|`.

Example:

Atelectasis|Effusion|Mass

becomes:

Atelectasis
Effusion
Mass

A `No Finding` record must not contain any other label.

## Metadata rule

Check:

- patient age
- patient gender
- view position
- duplicate image identifiers
- missing values
- missing image files
- ambiguous image matches

Ages outside 0–100 are flagged.

The source data can contain anomalous age values, so
the pipeline flags them instead of silently modifying them.

## Image QC rule

Automated heuristics include:

- blur
- contrast
- pixel clipping
- blankness
- corruption

These are dataset-QC indicators.

They are not clinical judgments.

## Review rule

Records flagged as:

- LOW_QUALITY
- MISSING_IMAGE
- AMBIGUOUS
- CORRUPT_IMAGE
- metadata-invalid

should be sent to human review.

Review decisions are outside the automated pipeline. The primary reporting
outputs are the Power BI-ready CSV files under `powerbi/nih_sample/`.