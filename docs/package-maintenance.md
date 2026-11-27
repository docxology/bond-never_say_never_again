# Maintain the never_say_never_again package

The distribution at this revision is `never_say_never_again` 0.1.0, with
Python compatibility `>=3.11`. This checkout selects Python 3.15 in [`.python-version`](../.python-version).
[Project metadata](../pyproject.toml) declares the package and compatibility.
[The lockfile](../uv.lock) records resolved dependency versions and sources.

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
