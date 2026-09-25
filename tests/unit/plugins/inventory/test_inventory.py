# SPDX-FileCopyrightText: Silex Data Solutions
# SPDX-License-Identifier: Apache-2.0
"""Unit tests for the silexdata.mysql.inventory inventory plugin.

The plugin is driven only through parse(), the way ansible-inventory drives it,
and the expectations come from its DOCUMENTATION and changelog rather than from
its implementation. pymysql.connect is replaced by a fake that keeps the
driver's documented contract - a DictCursor returns each row as a dict, errors
are pymysql.err exceptions, and a connection is the caller's to close - so a
failure here is the plugin's, not the fake's.
"""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

import pymysql
import pytest
from ansible.errors import AnsibleError
from ansible.inventory.data import InventoryData
from ansible.parsing.dataloader import DataLoader
from ansible.plugins.loader import inventory_loader

PLUGIN = "silexdata.mysql.inventory"
ENV = {
    "db_host": "MYSQL_INVENTORY_DB_HOST",
    "db_port": "MYSQL_INVENTORY_DB_PORT",
    "db_user": "MYSQL_INVENTORY_DB_USER",
    "db_password": "MYSQL_INVENTORY_DB_PASSWORD",
    "db_name": "MYSQL_INVENTORY_DB_NAME",
}
CONNECTION = [
    "db_host: db.example.com",
    "db_user: ansible",
    "db_password: s3cret",
    "db_name: cmdb",
]
ROWS = [
    {"hostname": "web-1", "fqdn": "web-1.example.com", "env": "DEV", "application": "web"},
    {"hostname": "db-1", "fqdn": "db-1.example.com", "env": "PROD", "application": "db"},
]


class FakeServer:
    """What the fake server returns, and every connection made to it."""

    def __init__(self):
        self.rows = [dict(row) for row in ROWS]
        self.error = None
        self.connections = []


class FakeConnection:
    def __init__(self, server, kwargs):
        self.server = server
        self.kwargs = kwargs
        self.queries = []
        self.closed = False

    def cursor(self):
        return FakeCursor(self)

    def close(self):
        self.closed = True


class FakeCursor:
    def __init__(self, connection):
        self.connection = connection

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def execute(self, query):
        self.connection.queries.append(query)
        if self.connection.server.error:
            raise self.connection.server.error

    def fetchall(self):
        # DictCursor: one dict per row, a fresh copy each time.
        return [dict(row) for row in self.connection.server.rows]


@pytest.fixture
def server(monkeypatch):
    for name in ENV.values():
        monkeypatch.delenv(name, raising=False)
    fake = FakeServer()

    def connect(**kwargs):
        connection = FakeConnection(fake, kwargs)
        fake.connections.append(connection)
        return connection

    monkeypatch.setattr(pymysql, "connect", connect)
    return fake


@pytest.fixture
def load(tmp_path):
    """Parse an inventory source written from `lines`; return the inventory."""

    def _load(lines, name="inventory.mysql.yml", cache=True, plugin=PLUGIN):
        source = tmp_path / name
        source.write_text(f"---\nplugin: {plugin}\n" + "".join(line + "\n" for line in lines))
        inventory = InventoryData()
        loaded = inventory_loader.get(PLUGIN)
        loaded.parse(inventory, DataLoader(), str(source), cache=cache)
        # What InventoryManager does after every parse(): persist the cache,
        # tolerating a plugin that has no cache loaded.
        try:
            loaded.update_cache_if_changed()
        except AttributeError:
            pass
        return inventory

    return _load


def query(sql):
    return [f"db_query: {sql}"]


def hostvars(inventory, host):
    return inventory.get_host(host).get_vars()


def hosts_of(inventory, group):
    return sorted(host.name for host in inventory.groups[group].get_hosts())


# verify_file ----------------------------------------------------------------


@pytest.mark.parametrize("name", ["inventory.mysql.yml", "inventory.mysql.yaml", "mysql.yml"])
def test_a_mysql_source_is_accepted(tmp_path, name):
    source = tmp_path / name
    source.write_text(f"---\nplugin: {PLUGIN}\n")
    assert inventory_loader.get(PLUGIN).verify_file(str(source))


@pytest.mark.parametrize("name", ["inventory.yml", "mysql.json", "hosts"])
def test_other_sources_are_left_to_other_plugins(tmp_path, name):
    source = tmp_path / name
    source.write_text(f"---\nplugin: {PLUGIN}\n")
    assert not inventory_loader.get(PLUGIN).verify_file(str(source))


# plugin -----------------------------------------------------------------------


@pytest.mark.parametrize("plugin", ["silexdata.mysql.inventory", "inventory"])
def test_each_documented_plugin_name_is_accepted(server, load, plugin):
    # DOCUMENTATION: choices: ['inventory', 'silexdata.mysql.inventory']
    inventory = load(CONNECTION + query("SELECT * FROM hosts"), plugin=plugin)
    assert sorted(inventory.hosts) == ["db-1", "web-1"]


# Connection options -------------------------------------------------------------


def test_the_connection_options_in_the_source_are_used(server, load):
    load(CONNECTION + ["db_port: 3307"] + query("SELECT * FROM hosts"))
    kwargs = server.connections[0].kwargs
    assert kwargs["host"] == "db.example.com"
    assert kwargs["port"] == 3307
    assert kwargs["user"] == "ansible"
    assert kwargs["password"] == "s3cret"
    assert kwargs["database"] == "cmdb"
    # Rows must come back as dicts, keyed by column.
    assert kwargs["cursorclass"] is pymysql.cursors.DictCursor


def test_the_port_defaults_to_3306(server, load):
    load(CONNECTION + query("SELECT * FROM hosts"))
    assert server.connections[0].kwargs["port"] == 3306


def test_the_connection_options_can_come_from_the_environment(server, load, monkeypatch):
    # 1.0.1: "Added environment variable option for db_host, db_port, db_user,
    # db_password, and db_name options."
    for option, value in {
        "db_host": "env-db.example.com",
        "db_port": "3308",
        "db_user": "env-user",
        "db_password": "env-secret",
        "db_name": "env-cmdb",
    }.items():
        monkeypatch.setenv(ENV[option], value)
    load(query("SELECT * FROM hosts"))
    kwargs = server.connections[0].kwargs
    assert (kwargs["host"], kwargs["port"], kwargs["user"], kwargs["password"], kwargs["database"]) == (
        "env-db.example.com",
        3308,
        "env-user",
        "env-secret",
        "env-cmdb",
    )


@pytest.mark.parametrize("missing", ["db_host", "db_user", "db_password", "db_name"])
def test_each_required_connection_option_is_required(server, load, missing):
    lines = [line for line in CONNECTION if not line.startswith(missing + ":")]
    with pytest.raises(Exception) as caught:
        load(lines + query("SELECT * FROM hosts"))
    assert missing in str(caught.value)
    assert not server.connections


# The query ----------------------------------------------------------------------


def test_the_query_runs_as_written_and_the_connection_is_closed(server, load):
    load(CONNECTION + query("SELECT name AS hostname FROM hosts WHERE active = 1"))
    (connection,) = server.connections
    assert connection.queries == ["SELECT name AS hostname FROM hosts WHERE active = 1"]
    assert connection.closed


def test_a_lowercase_select_is_a_select(server, load):
    inventory = load(CONNECTION + query("select * from hosts"))
    assert sorted(inventory.hosts) == ["db-1", "web-1"]


@pytest.mark.parametrize("sql", ["DELETE FROM hosts", "UPDATE hosts SET env = 'X'", "DROP TABLE hosts"])
def test_a_query_that_is_not_a_select_is_refused_without_connecting(server, load, sql):
    with pytest.raises(AnsibleError, match="SELECT"):
        load(CONNECTION + query(sql))
    assert not server.connections


def test_an_empty_query_is_refused_without_connecting(server, load):
    with pytest.raises(AnsibleError):
        load(CONNECTION + ['db_query: "   "'])
    assert not server.connections


def test_a_database_error_fails_the_inventory_and_closes_the_connection(server, load):
    server.error = pymysql.err.ProgrammingError(1146, "Table 'cmdb.hosts' doesn't exist")
    with pytest.raises(AnsibleError) as caught:
        load(CONNECTION + query("SELECT * FROM hosts"))
    assert "Table 'cmdb.hosts' doesn't exist" in str(caught.value)
    assert server.connections[0].closed


# Rows become hosts --------------------------------------------------------------


def test_each_row_becomes_a_host_with_its_columns_as_variables(server, load):
    inventory = load(CONNECTION + query("SELECT * FROM hosts"))
    assert sorted(inventory.hosts) == ["db-1", "web-1"]
    assert hosts_of(inventory, "all") == ["db-1", "web-1"]
    web = hostvars(inventory, "web-1")
    assert (web["fqdn"], web["env"], web["application"]) == ("web-1.example.com", "DEV", "web")


def test_hostname_field_chooses_the_column_that_names_the_host(server, load):
    inventory = load(CONNECTION + query("SELECT * FROM hosts") + ["hostname_field: fqdn"])
    assert sorted(inventory.hosts) == ["db-1.example.com", "web-1.example.com"]


def test_a_row_without_a_hostname_is_skipped(server, load):
    server.rows.append({"hostname": None, "fqdn": "nameless.example.com", "env": "DEV", "application": "web"})
    inventory = load(CONNECTION + query("SELECT * FROM hosts"))
    assert sorted(inventory.hosts) == ["db-1", "web-1"]


# constructed ------------------------------------------------------------------


def test_keyed_groups_group_hosts_by_their_columns(server, load):
    inventory = load(CONNECTION + query("SELECT * FROM hosts") + ["keyed_groups:", "  - key: application", "    prefix: app"])
    assert hosts_of(inventory, "app_web") == ["web-1"]
    assert hosts_of(inventory, "app_db") == ["db-1"]


def test_groups_add_hosts_by_condition(server, load):
    inventory = load(CONNECTION + query("SELECT * FROM hosts") + ["groups:", '  prod: "env == \'PROD\'"'])
    assert hosts_of(inventory, "prod") == ["db-1"]


def test_compose_sets_variables_from_expressions(server, load):
    inventory = load(CONNECTION + query("SELECT * FROM hosts") + ["compose:", "  site: application ~ '-' ~ env"])
    assert hostvars(inventory, "web-1")["site"] == "web-DEV"


def test_compose_tolerates_an_undefined_variable_unless_strict(server, load):
    inventory = load(CONNECTION + query("SELECT * FROM hosts") + ["compose:", "  owner_name: owner.name"])
    assert "owner_name" not in hostvars(inventory, "web-1")


def test_compose_fails_on_an_undefined_variable_when_strict(server, load):
    with pytest.raises(AnsibleError):
        load(CONNECTION + query("SELECT * FROM hosts") + ["strict: true", "compose:", "  owner_name: owner.name"])


# inventory_cache ----------------------------------------------------------------


@pytest.fixture
def cached(tmp_path):
    return [
        "cache: true",
        "cache_plugin: ansible.builtin.jsonfile",
        f"cache_connection: {tmp_path / 'cache'}",
    ]


def test_a_cached_inventory_is_served_without_querying(server, load, cached):
    first = load(CONNECTION + query("SELECT * FROM hosts") + cached)
    second = load(CONNECTION + query("SELECT * FROM hosts") + cached)
    assert len(server.connections) == 1, "the second parse queried the database instead of the cache"
    assert sorted(second.hosts) == sorted(first.hosts)


def test_a_cache_refresh_queries_again_and_updates_the_cache(server, load, cached):
    # cache=False is ansible-inventory's --flush-cache: query afresh, and store
    # the result so later cached runs see it.
    load(CONNECTION + query("SELECT * FROM hosts") + cached)
    server.rows.append({"hostname": "app-1", "fqdn": "app-1.example.com", "env": "QA", "application": "app"})
    refreshed = load(CONNECTION + query("SELECT * FROM hosts") + cached, cache=False)
    assert "app-1" in refreshed.hosts
    later = load(CONNECTION + query("SELECT * FROM hosts") + cached)
    assert len(server.connections) == 2, "the cached run after a refresh queried the database again"
    assert "app-1" in later.hosts, "the refresh did not update the cache"


def test_caching_is_off_by_default(server, load):
    load(CONNECTION + query("SELECT * FROM hosts"))
    load(CONNECTION + query("SELECT * FROM hosts"))
    assert len(server.connections) == 2
