# Datasheet — chest_condition

## Dataset purpose

This project creates an image-centric dataset manifest by joining source metadata and image-level labels to locally available image files. It then applies automated metadata, image-quality, duplicate and dataset-integrity checks.

## Label source

`csv`

## Annotation scope

The supplied label files contain image-level labels. Unless a separate bounding-box or segmentation annotation file is available, these labels are not treated as lesion coordinates, bounding boxes or segmentation masks.

## Dataset coverage

Metadata records: 111,010

Images matched to local files: 3,681

Metadata records without local images: 107,329

Ambiguous image matches: 0

Orphan local images: 29

Missing local images are retained in the manifest because the metadata record exists even though the corresponding image asset is unavailable in the local subset.

## Metadata QC summary

Invalid age: 0

Invalid gender: 0

Invalid view position: 0

Unknown label spelling: 0

No Finding conflicts: 0

Empty labels: 0

Duplicate metadata records: 0

## Automated image QC

For locally available and readable images, the pipeline calculates image dimensions, blur/sharpness indicators, contrast, pixel clipping, non-zero pixel ratio and readability. It also calculates SHA-256, perceptual and difference hashes for duplicate analysis.

## Duplicate analysis

Exact duplicate detection uses SHA-256 file hashes. Perceptual hashing is used to identify near-duplicate candidates. Near-duplicate candidates require review and are not automatically treated as erroneous records.

## Human review

The reviewer interface records reviewer identity, decision, reason codes and comments. Review decisions can be compared across reviewers to measure agreement.

## Privacy

Treat all image data and metadata as sensitive. Keep raw data local, do not publish identifiable content, and follow the source dataset's usage and privacy requirements.

## Known limitations

Automated thresholds are heuristic and should be tuned using a representative human-reviewed sample. QC flags identify records for review; they do not establish clinical meaning or provide a medical diagnosis.

The current local image collection may represent only a subset of the records described by the metadata file. Therefore missing-image counts should be interpreted as local asset availability findings.
