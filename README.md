# Medical Image Annotation and Dataset Quality Pipeline

This project checks medical-image datasets for metadata and image-quality problems. It does not diagnose disease or determine clinical truth.

## What it does

For each dataset, the pipeline:

1. Reads the metadata CSV.
2. Matches metadata rows to local image files.
3. Validates age, gender, view position, labels, duplicates, and missing images.
4. Reads image pixels with OpenCV.
5. Calculates image-quality metrics such as blur, contrast, entropy, clipping, noise, edges, resolution, background, and borders.
6. Detects exact and visually similar duplicates.
7. Calculates a quality score and assigns `PASS`, `REVIEW`, or `UNAVAILABLE`.
8. Exports CSV, Excel, charts, anomaly results, patient groups, feature clusters, and Power BI tables.

## Run

From the project root:

```powershell
$env:PYTHONPATH = (Get-Location).Path
uv run pytest -q
uv run python -m src.nih_sample.run_pipeline --config configs/nih_sample.yaml
uv run python -m src.chest_condition.run_pipeline --config configs/chest_condition.yaml
```

## Main outputs

Each dataset writes to `data/<dataset>/processed/`:

- `manifest.csv`: metadata-to-image connections
- `image_metrics.csv`: pixel and image measurements
- `duplicates.csv`: exact and near-duplicate candidates
- `validation_issues.csv`: metadata and matching issues
- `cleaned_manifest.csv`: final table with QC status and quality score
- `quality_report.xlsx`: Excel workbook with summary sheets
- `quality_outputs/`: status splits, metadata errors, summaries, and schema drift
- `ml/`: anomaly scores, patient groups, and feature clusters

## Power BI

Power BI-ready tables are exported to:

```text
powerbi/nih_sample/
powerbi/chest_condition/
```

Open `powerbi/POWER_BI_GUIDE.md` for the recommended report pages, tables, relationships, and refresh workflow. The `.pbix` file must be created and saved in Power BI Desktop because Power BI Desktop owns the visual report file format.

Use `cleaned_manifest.csv` as the central table. Use `image_id` as its key for image-level tables. Keep `Patient ID` and `image_id` as text when leading zeroes matter.

## Status meanings

- `PASS`: automated checks found no configured issue.
- `REVIEW`: automated checks found an issue requiring investigation.
- `UNAVAILABLE`: metadata exists but the image is not in the local image subset.

## Limitations

Advanced medical-vision tasks such as lung segmentation, AP/PA classification, image registration, and text-marker detection require suitable labeled data or validated pretrained models. The current pipeline does not pretend that simple heuristics are clinical models.
