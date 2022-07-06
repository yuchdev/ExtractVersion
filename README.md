## Extract Version

![license](https://img.shields.io/github/license/yuchdev/ExtractVersion)
![workflow](https://github.com/yuchdev/ExtractVersion/actions/workflows/python-app.yml/badge.svg)
![issues](https://img.shields.io/github/issues/yuchdev/ExtractVersion)

Python module for extracting version from the string or directory name.
Could make use for creating an inventory of installed versions of a particular application 
or finding the latest installed version.

The module offers the following functionality:
* Fetching version string from the string or name of the directory
* Validating version string
* Sorting config and application directories that contain versions in its name

### Examples:

1. We fetch version `2020.1.0` from string `PyCharm-2020.1.0`, or version `1.0` from `my_program_v1.0`

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

3. In edge cases with more than one pattern present, e.g. `PyCharm-2018.1.2-windows-10.0`, 
we should provide a clue where the version should be extracted from, 
in a form of a pattern-regex, e.g.`PyCharm-(.*)-windows-10.0`
The call of such function may look like this:

```python
extract_version(version_string='PyCharm-2018.1.2-windows-10.0', pattern='PyCharm-(.*)-windows-10.0')
> "2018.1.2"
```

4. Create an inventory of installed versions of a particular application
```python
application_path = "C:/Users/user/AppData/Local/JetBrains/PyCharm"
pycharm_versions = available_versions(versions_path=application_path)
> {"2018.1.2": "PyCharm-2018.1.2", "2018.2.0": "PyCharm-2018.2.0", "2020.1.0": "PyCharm-2020.1.0"}
```
