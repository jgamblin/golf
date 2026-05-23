# Changelog

## 2026-05-23

- Fixed CSV timestamp parsing in ingest to support Garmin AM/PM formats (for example, `05/23/26 08:27:28 AM`) in addition to 24-hour timestamps.
- Added regression coverage to prevent `did not contain any shot rows` failures caused by valid AM/PM session rows being skipped.
