# devpi-timemachine

`devpi-timemachine` is a `devpi` plugin that allows you to `pip install` (and
other similar Python package installation commands) packages as if you were
doing so on a previous date in time. Time travel into the future to install
not-yet-released packages is not supported (yet).

## Usage

1. Install `devpi` and `devpi-timemachine`.
2. Create a new `devpi` index. There are three important options to use here.
   See below for an example command and explanation of these options.
3. Specify your new index when using pip.

```
$ devpi index -c 20200101 type=timemachine bases=/root/pypi
$ pip install --index-url http://localhost:3141/root/20200101/+simple/ requests
$ pip list  # Notice that these installed versions are from 2019, not 2023
Package    Version
---------- ----------
certifi    2019.11.28
chardet    3.0.4
idna       2.8
pip        23.1.2
requests   2.22.0
setuptools 67.7.2
urllib3    1.25.7
wheel      0.40.0
```

These options do the following:

- The index name ("20200101" in this example) must be a date parseable by
  `datetime.fromisoformat`. This date is used as the cutoff date for allowing
  package versions through the proxy. This is the mechanism by which you can
  configure `devpi-timemachine` (and the only real configuration option). The
  time machine plugin uses this date and PyPI file upload times to choose which
  releases to filter and to emulate what was available on PyPI at a given point
  in time.

- `type=timemachine` instructs devpi to create the index with the "timemachine"
  type, which automatically loads the `devpi-timemachine` plugin. No other
  configuration is necessary to enable the plugin.

- `bases=/root/pypi` configures the index to inherit from the `/root/pypi`
  index. I recommend using this option (or using another base that inherits from
  PyPI), as the date filtering is based on PyPI metadata, but it may in theory
  work with other bases as well.

## Motivation

Ideally, upgrading project dependencies is done early and often to reduce the
upgrade burden at any given point. This is not always possible, and upgrading an
older project by several years all in one swoop can be difficult. You can make
these changes in smaller chunks by explicitly upgrading major dependencies to
intermediate versions until you get to your target set of dependencies, but this
may result in installing incompatible dependencies, especially in the case of
dependency X setting a minimum version but not a maximum version for its own
dependency Y. The `devpi-timemachine` approach allows you to upgrade all of your
dependencies up to a calendar date you choose to reduce this possibility; this
plugin can be used to simulate your desired practice of upgrading dependencies
on a cadence, e.g. monthly.

## Status

This is a proof of concept at this stage. Anecdotal testing and development
shows that is works as intended, but I'm sure there are limitations, bugs, and
edge cases that are not accounted for here.
