# QC flag reason codes

Shared codes used in manifests, review decisions and reports.

| Code | Meaning |
|---|---|
| LOW_QUALITY | Image falls below one or more automated image-quality thresholds. |
| AMBIGUOUS | More than one local image candidate matched the metadata record. |
| MISSING_IMAGE | CSV metadata record has no corresponding local image. |
| ORPHAN_IMAGE | Local image has no corresponding CSV metadata record. |
| CORRUPT_IMAGE | File exists but cannot be decoded as an image. |
| DUPLICATE | Exact duplicate detected by SHA-256. |
| NEAR_DUPLICATE | Candidate visually similar image detected using perceptual hash. |
| INVALID_AGE | Age is missing, negative, or outside the configured plausibility range. |
| INVALID_GENDER | Gender value is missing or outside the configured allowed set. |
| INVALID_VIEW | View position is missing or outside the configured allowed set. |
| NO_FINDING_CONFLICT | `No Finding` appears together with another label. |
| EMPTY_LABEL | Label field is empty or missing. |
| LABEL_SPELLING | Label is not in the approved vocabulary. |
| METADATA_DUPLICATE | Same image identifier occurs more than once in metadata. |
| REVIEW_REQUIRED | Automated checks require human review. |
| ACCEPTED | Human reviewer accepted the record. |
| REJECTED | Human reviewer rejected the record. |