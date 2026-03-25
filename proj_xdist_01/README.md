# Why?

I want to try some things with `pytest` and `pytest-xdist` and keep a record.

## Init

Initialized from the repo root level (`learn-pytest`) with:
```bash
uv init --app --bare --no-readme --python ">=3.13,<3.14" proj_xdist_01
```

The Python version is pinned in order to be compatible with another project.

## Dependencies

Per [the uv docs](https://docs.astral.sh/uv/concepts/projects/dependencies/), the following types of dependencies have different meanings:
  * project dependencies
    * The `project.dependencies` table represents the dependencies that are used when uploading to PyPI or building a wheel.
    * `project.dependencies` defines the list of packages that are required for the project, along with the version constraints that should be used when installing them. Each entry includes a dependency name and version. An entry may include extras or environment markers for platform-specific packages.
  * optional dependencies
    * It is common for projects that are published as libraries to make some features optional to reduce the default dependency tree. For example, Pandas has an excel extra and a plot extra to avoid installation of Excel parsers and matplotlib unless someone explicitly requires them. Extras are requested with the `package[<extra>]` syntax, e.g., `pandas[plot, excel]`.
    * Optional dependencies are specified in `[project.optional-dependencies]`, a TOML table that maps from extra name to its dependencies
  * development dependencies
    * Unlike optional dependencies, development dependencies are local-only and will not be included in the project requirements when published to PyPI or other indexes.
  * build dependencies
    * If a project is structured as Python package, it may declare dependencies that are required to build the project, but not required to run it. These dependencies are specified in the `[build-system]` table under `build-system.requires`, following PEP 518.


### Add "optional dependencies"

Add some "optional dependencies" for testing purposes:

```bash
uv add pytest pytest-xdist --optional dev
```

This would add this section to `pyproject.toml`:
```toml
[project.optional-dependencies]
dev = [
    "pytest>=9.0.2",
    "pytest-xdist>=3.8.0",
]
```


## Example `pytest` command with `-n`

Running `pytest` from the `proj_xdist_01` folder with:

```bash
uv run pytest --durations=0 --durations-min=0.01 -v tests/xdist_with_hooks -n auto
```
