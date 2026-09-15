# 01 - Config model

**Parent task:** [README.md](README.md)
**Status:** ⬜ Not started

## Requirements

- Add a `HealthConfig` settings model with a `service_name: str` field,
  defaulting to `"extract_version"`.
- Load it the same way other config sections are loaded in this project.

## Files

- `src/extract_version/config/health.py` - new `HealthConfig` model.
- `tests/unit/test_health_config.py` - default value + override test.
