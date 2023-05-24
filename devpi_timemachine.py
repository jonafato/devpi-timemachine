from datetime import datetime, timezone

from devpi_server.model import BaseStageCustomizer
from packaging.version import parse as parse_version, InvalidVersion
from packaging.utils import (
    InvalidSdistFilename,
    InvalidWheelFilename,
    parse_sdist_filename,
    parse_wheel_filename,
)
import pluggy
import requests

hookimpl = pluggy.HookimplMarker("devpiserver")
api_url = "https://pypi.org/simple/{project}/"


class TimeMachineCustomizer(BaseStageCustomizer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.project_versions = {}

    def release_dates_for_project(self, project):
        if project not in self.project_versions:
            resp = requests.get(
                api_url.format(project=project),
                headers={"Accept": "application/vnd.pypi.simple.v1+json"},
            )
            release_dates = {}
            for entry in resp.json()["files"]:
                try:
                    try:
                        _, version = parse_sdist_filename(entry["filename"])
                    except InvalidSdistFilename:
                        try:
                            _, version, _, _ = parse_wheel_filename(entry["filename"])
                        except InvalidWheelFilename:
                            continue
                except InvalidVersion:
                    continue

                # If any file was available for a version, consider that
                # version for the specified date.
                version_date = datetime.fromisoformat(entry["upload-time"])
                if version in release_dates:
                    release_dates[version] = min(
                        release_dates[version],
                        version_date,
                    )
                else:
                    release_dates[version] = version_date

            self.project_versions[project] = release_dates

        return self.project_versions[project]

    # TODO: Do I actually need to implement get_projects_filter_iter and
    # get_versions_filter_iter? Should be easy enough to do, but my
    # testing with pip and pip-compile so far seems to work with just
    # get_simple_links_filter_iter.

    def get_simple_links_filter_iter(self, project, links):
        cutoff = datetime.fromisoformat(self.stage.index).replace(tzinfo=timezone.utc)
        project_versions = self.release_dates_for_project(project)
        for link in links:
            # If the version we're trying to compare to is invalid,
            # remove it from consideration.
            try:
                version = parse_version(link.version)
            except InvalidVersion:
                yield False
                continue

            # If the version we've parsed is missing from the release
            # dates mapping, there was likely an error in parsing the
            # version returned by the upstream index server. In my
            # anecdotal testing, this can occur with very old versions
            # of some packages (likely predating PEP 440). I would like
            # to figure out the best way to support this correctly, but
            # for now, we'll drop versions that use identifiers that
            # cannot be parsed by modern tooling.
            if version not in project_versions:
                yield False
                continue

            yield project_versions[parse_version(link.version)] <= cutoff


@hookimpl
def devpiserver_get_stage_customizer_classes():
    return [("timemachine", TimeMachineCustomizer)]
