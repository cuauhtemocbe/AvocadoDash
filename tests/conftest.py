"""Fixtures for driving the real Dash callback pipeline over HTTP, no browser.

`app.server` is a Flask app, so its test client can call the very endpoints a
browser calls — `/_dash-layout`, `/_dash-dependencies` and
`/_dash-update-component` — in-process. Requests are built from
`/_dash-dependencies` rather than hard-coded, so a wrong Input/Output id shows
up as a failing test instead of a silently stale fixture.
"""

from typing import Any

import pytest
from flask.testing import FlaskClient

from app import app

# What the clientside theme callback resolves on load. It has no layout
# default (the store starts empty), so a request has to say it explicitly.
VALUES_NOT_IN_LAYOUT = {"theme-resolved.data": "light"}

# Component properties worth reading a default from. Anything else in the tree
# (children, className, options...) is never a callback Input/State here.
STATE_PROPS = ("value", "start_date", "end_date", "data", "search", "n_clicks")


def split_output(output: str) -> list[str]:
    """`..a.b...c.d..` (multi-output) or `a.b` -> the list of `id.property`."""
    if output.startswith(".."):
        return output[2:-2].split("...")
    return [output]


def walk_components(node: Any) -> list[dict[str, Any]]:
    """Every component dict in a serialized `/_dash-layout` tree."""
    found: list[dict[str, Any]] = []
    if isinstance(node, dict):
        if "props" in node and "type" in node:
            found.append(node)
        for value in node.values():
            found.extend(walk_components(value))
    elif isinstance(node, list):
        for item in node:
            found.extend(walk_components(item))
    return found


class DashClient:
    def __init__(self, client: FlaskClient) -> None:
        self._client = client
        self.layout: dict[str, Any] = self._get_json("/_dash-layout")
        self.dependencies: list[dict[str, Any]] = self._get_json("/_dash-dependencies")

        self.layout_ids: set[str] = set()
        self.defaults: dict[str, Any] = dict(VALUES_NOT_IN_LAYOUT)
        for component in walk_components(self.layout):
            component_id = component["props"].get("id")
            if not isinstance(component_id, str):
                continue
            self.layout_ids.add(component_id)
            for prop in STATE_PROPS:
                if prop in component["props"]:
                    self.defaults.setdefault(
                        f"{component_id}.{prop}", component["props"][prop]
                    )

    def _get_json(self, path: str) -> Any:
        response = self._client.get(path)
        assert response.status_code == 200, path
        return response.get_json()

    def ids_missing_from_layout(self) -> set[str]:
        """Component ids that a callback Input/State/Output points at but
        that `/_dash-layout` doesn't contain."""
        missing: set[str] = set()
        for dependency in self.dependencies:
            ids = {item["id"] for item in dependency["inputs"] + dependency["state"]}
            ids |= {p.partition(".")[0] for p in split_output(dependency["output"])}
            missing |= ids - self.layout_ids
        return missing

    def callback_for(self, output_prop: str) -> dict[str, Any]:
        """The registered callback that writes `id.property`."""
        matches = [
            dependency
            for dependency in self.dependencies
            if output_prop in split_output(dependency["output"])
        ]
        assert len(matches) == 1, f"{output_prop}: {len(matches)} callbacks write it"
        return matches[0]

    def post(
        self,
        output_prop: str,
        values: dict[str, Any] | None = None,
        changed: list[str] | None = None,
    ) -> Any:
        """POST to `/_dash-update-component` for the callback writing
        `output_prop`. Inputs/State take `values` (keyed `id.property`), then
        the layout's default, so a request only states what it changes.
        `changed` becomes `changedPropIds` (what `ctx.triggered_id` reads)."""
        dependency = self.callback_for(output_prop)
        wanted = [
            *(f"{item['id']}.{item['property']}" for item in dependency["inputs"]),
            *(f"{item['id']}.{item['property']}" for item in dependency["state"]),
        ]
        unknown = set(values or {}) - set(wanted)
        assert not unknown, f"not an Input/State of {output_prop}: {sorted(unknown)}"

        merged = {**self.defaults, **(values or {})}

        def with_value(item: dict[str, Any]) -> dict[str, Any]:
            return {**item, "value": merged.get(f"{item['id']}.{item['property']}")}

        outputs = []
        for prop_key in split_output(dependency["output"]):
            component_id, _, prop = prop_key.partition(".")
            outputs.append({"id": component_id, "property": prop})

        body = {
            "output": dependency["output"],
            "outputs": outputs if len(outputs) > 1 else outputs[0],
            "inputs": [with_value(item) for item in dependency["inputs"]],
            "state": [with_value(item) for item in dependency["state"]],
            "changedPropIds": changed or [],
        }
        return self._client.post("/_dash-update-component", json=body)

    def call(
        self,
        output_prop: str,
        values: dict[str, Any] | None = None,
        changed: list[str] | None = None,
    ) -> dict[str, Any]:
        """Like `post`, but asserts a 200 and flattens the response to
        `{"id.property": value}`. Outputs the callback left as `no_update`
        are absent from Dash's response, hence absent here."""
        response = self.post(output_prop, values, changed)
        assert response.status_code == 200, response.get_data(as_text=True)
        return {
            f"{component_id}.{prop}": value
            for component_id, props in response.get_json()["response"].items()
            for prop, value in props.items()
        }

    def figure(
        self,
        output_prop: str,
        values: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        figure: dict[str, Any] = self.call(output_prop, values)[output_prop]
        return figure


@pytest.fixture(scope="session")
def dash_client() -> DashClient:
    return DashClient(app.server.test_client())
