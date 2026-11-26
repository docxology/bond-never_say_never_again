# Maintain the never_say_never_again package

[Project metadata](../pyproject.toml) declares the package identity and Python
compatibility (`>=3.11`). [The lockfile](../uv.lock) records resolved
dependencies. Compare these two files when checking package metadata.

## Dependency provenance

- `bond-api` resolves to a sibling checkout at `../bond-api`. The
  lockfile records the relative path. A different checkout at that
  path can supply different source bytes.

## Citation and release records

[Citation metadata](../CITATION.cff), [CodeMeta](../codemeta.json), and
[Zenodo metadata](../.zenodo.json) describe this package. Check the
version fields that are present against the project metadata. A repository
metadata file does not establish that a release has been deposited.

For a documentation review, run `git diff --check` and verify the relative
links added by the change against the tracked checkout. These checks
provide evidence about the documentation and package records.
