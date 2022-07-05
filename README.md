## Extract Version

Python module for extracting version from the string or directory name

The module offers following functionality:
* Fetching version string from the string or name of the directory
* Validating version string
* Sorting config and application directories that contain versions in its name

### Examples:

1. We fetch version `2020.1.0` from string `PyCharm-2020.1.0`, or version `1.0` from `my_program_v1.0`.

* `AppVersion.Major.Minor` version format

```python
extract_version(version_string="PyCharm-2020.1.0")
> "2020.1.0"
```
* `Major.Minor` version format

```python
extract_version(version_string="my_program_v1.0")
> "1.0"
```

2. Sort directories by the version of application

```python
sort_versions(["PyCharm-2018.1.2", "PyCharm-2018.2.0", "PyCharm-2020.1.0"])
> ["PyCharm-2018.1.2", "PyCharm-2018.2.0", "PyCharm-2020.1.0"]
```

3. In edge cases with more than one pattern, e.g. `PyCharm-2018.1.2-windows-10.0`, 
we should provide a clue where the version should be extracted from, 
in a form of a pattern-regex, e.g.`PyCharm-(.*)-windows-10.0`
Call of such function may look like:

```python
extract_version(version_string='PyCharm-2018.1.2-windows-10.0', pattern='PyCharm-(.*)-windows-10.0')
> "2018.1.2"
```
