# Medical Image Annotation and Dataset Quality Pipeline

A Python pipeline for medical-image metadata validation, image-quality analysis,
duplicate detection, anomaly analysis, reporting, and Power BI dataset-quality
visualization. It does not diagnose disease or determine clinical truth.

## Datasets

Download the datasets before running the pipeline:

1. [Chest X-ray Dataset](https://www.kaggle.com/datasets/rishabhrp/chest-x-ray-dataset)
2. [NIH Chest X-rays Sample](https://www.kaggle.com/datasets/nih-chest-xrays/sample)

Keep the downloaded image files in the configured image folders. The metadata
CSV files are included in the repository; raw image files are intentionally
excluded from GitHub because of their size.

Expected dataset locations:

data/Chest_XRay_Dataset/Ground_Truth.csv
data/Chest_XRay_Dataset/xray_images/
data/nih_sample/raw/sample_labels.csv
data/nih_sample/raw/images/

## What it does

For each dataset, the pipeline:

1. Reads the metadata CSV.
2. Matches metadata rows to local image files.
3. Validates age, gender, view position, labels, duplicates, and missing images.
4. Reads image pixels with OpenCV.
5. Calculates image-quality metrics such as blur, contrast, entropy, clipping,
	noise, edges, resolution, background, borders, and pixel statistics.
6. Detects exact and visually similar duplicates.
7. Calculates a quality score and assigns `PASS`, `REVIEW`, or `UNAVAILABLE`.
8. Exports CSV, Excel, charts, anomaly results, patient groups, feature
	clusters, and Power BI tables.

## Setup and Run

From the project root:

uv sync
$env:PYTHONPATH = (Get-Location).Path
uv run pytest -q
uv run python -m src.nih_sample.run_pipeline --config configs/nih_sample.yaml
uv run python -m src.chest_condition.run_pipeline --config configs/chest_condition.yaml

Run either dataset pipeline independently. The pipelines process local images;
they do not download data automatically.

## Main Outputs

Each dataset writes detailed results to `data/<dataset>/processed/`:

- `manifest.csv`: metadata-to-image connections
- `image_metrics.csv`: image dimensions, pixel statistics, and quality metrics
- `duplicates.csv`: exact and near-duplicate candidates
- `validation_issues.csv`: metadata and matching issues
- `cleaned_manifest.csv`: final table with QC status and quality score
- `quality_report.xlsx`: Excel workbook with summary worksheets
- `quality_outputs/`: status splits, metadata errors, summaries, and schema drift
- `ml/`: anomaly scores, patient groups, and feature clusters

Additional generated reports are written to:

- `reports/datasheets/`
- `reports/visualizations/`
- `reports/duplicate_comparisons/`
- `outputs/metadata_schema.json`

## Power BI

Power BI-ready tables are exported to:

powerbi/nih_sample/
powerbi/chest_condition/

Each folder contains the dashboard CSV tables. The Power BI guide is at
`powerbi/POWER_BI_GUIDE.md`. The visual `.pbix` report is created and saved in
Power BI Desktop because Power BI owns that report format.

Use `cleaned_manifest.csv` as the central table. Use `image_id` as its key for
image-level tables. Keep `Patient ID` and `image_id` as text when leading
zeroes must be preserved.

## Status Meanings

- `PASS`: automated checks found no configured issue.
- `REVIEW`: automated checks found an issue requiring investigation.
- `UNAVAILABLE`: metadata exists but the image is not in the local image subset.

## Limitations

The current pipeline performs dataset quality control. It does not perform
clinical interpretation, lung segmentation, image registration, image-based
AP/PA classification, text or marker detection, or automatic diagnosis. Those
features require additional validated models, suitable labeled data, and
medical expert review.
