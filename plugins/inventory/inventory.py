# Copyright: (c) 2025, Adam Brauns (@AdamBrauns)
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

DOCUMENTATION = r"""
name: inventory
short_description: Dynamically builds Ansible inventory from a MySQL query
description:
  - Dynamically generate Ansible inventory by running a custom SQL SELECT query on a
    MySQL database.
  - Each row from the query is mapped to an inventory host, with fields as host variables.
  - Useful for environments where host data is stored in a database and needs to sync
    with Ansible inventory.
  - Supports inventory caching, custom hostname field mapping, and constructed inventory
    features.
version_added: "1.0.0"
requirements:
  - pymysql
extends_documentation_fragment:
  - constructed
  - inventory_cache
author:
  - Adam Brauns (@abrauns-silex)
  - Kevin Pavon (@kpavon-silex)
options:
  plugin:
    description:
      - Name of the plugin
    required: true
    type: list
    elements: str
    choices: ['inventory', 'silexdata.mysql.inventory']
  db_host:
    description:
      - Database host
    required: true
    type: str
  db_port:
    description:
      - Database port
    required: false
    default: 3306
    type: int
  db_user:
    description:
      - Database user
    required: true
    type: str
  db_password:
    description:
      - Database password
    required: true
    type: str
  db_name:
    description:
      - Database name
    required: true
    type: str
  db_query:
    description:
      - Database query
    required: true
    type: str
  hostname_field:
    description:
      - Database field that should be mapped to inventory_hostname
    required: false
    type: str
    default: hostname
  cache:
    description:
      - Enable inventory caching for this plugin
    required: false
    type: bool
    default: false
"""

EXAMPLES = r"""
plugin: silexdata.mysql.inventory

strict: false

db_host: localhost
db_user: ansible
db_password: ansiblepass
db_name: master
db_query: |
    SELECT * FROM mydb;

hostname_field: hostname

keyed_groups:
  - key: application
    prefix: app_
    separator: ""

groups:
  sbox: "env == 'SAND'"
  dev: "env == 'DEV'"
  test: "env == 'TEST'"
  qa: "env == 'QA'"
  prod: "env == 'PROD'"
"""

import pymysql
from ansible.errors import AnsibleError
from ansible.module_utils.common.text.converters import to_native
from ansible.plugins.inventory import BaseInventoryPlugin, Cacheable, Constructable
from ansible.utils.display import Display

# Initialize Display instance
display = Display()


class InventoryModule(BaseInventoryPlugin, Constructable, Cacheable):
    NAME = "mysql"

    def verify_file(self, path):
        valid = False
        if super().verify_file(path):
            if path.endswith(("mysql.yaml", "mysql.yml")):
                valid = True
        display.vv(f"Verifying inventory file: {path}, Valid: {valid}")
        return valid

    def parse(self, inventory, loader, path, cache=True):
        super().parse(inventory, loader, path, cache)

        self._read_config_data(path)
        display.vv(f"Parsing inventory file: {path}")

        cache_key = self.get_cache_key(path)

        user_cache_setting = self.get_option("cache")
        utilize_cache = user_cache_setting and cache
        display.vv(f"Utilize cache: {utilize_cache}")

        raw_hosts = None
        if utilize_cache:
            try:
                raw_hosts = self._cache[cache_key]
                display.vv(f"Cache hit for key: {cache_key}")
            except KeyError:
                display.vv(f"Cache miss for key: {cache_key}")

        if raw_hosts is None:
            display.vv("No cached data found, querying database")
            raw_hosts = self._get_raw_hosts()
            if utilize_cache:
                self._cache[cache_key] = raw_hosts
                display.vv(f"Cached data for key: {cache_key}")

        display.vv(f"Populating inventory with {len(raw_hosts)} hosts")
        self._populate(raw_hosts)

    def _get_raw_hosts(self):
        connection = None

        query = self.get_option("db_query")
        if not isinstance(query, str) or not query.strip():
            error = "Query must be a non-empty string"
            display.error(error)
            raise AnsibleError(error)
        if not query.strip().upper().startswith("SELECT"):
            error = "Database query must be a valid SELECT statement"
            display.error(error)
            raise AnsibleError(error)

        try:
            connection = pymysql.connect(
                host=self.get_option("db_host"),
                port=int(self.get_option("db_port")),
                user=self.get_option("db_user"),
                password=self.get_option("db_password"),
                database=self.get_option("db_name"),
                cursorclass=pymysql.cursors.DictCursor,
            )
            display.vv(
                f"Connected to database: {self.get_option('db_name')} on {self.get_option('db_host')}"
            )

            with connection.cursor() as cursor:
                display.vvv(f"Executing query: {query}")
                cursor.execute(query)
                raw_hosts = cursor.fetchall()
                display.vv(f"Fetched {len(raw_hosts)} rows from database")
                return raw_hosts

        except Exception as e:
            error = f"Database query failed: {to_native(e)}"
            display.error(error)
            raise AnsibleError(error)

        finally:
            if connection:
                connection.close()
                display.vv("Closed database connection")

    def _populate(self, raw_hosts):
        hostname_field = self.get_option("hostname_field")
        display.vvv(f"Using hostname field: {hostname_field}")
        for row in raw_hosts:
            try:
                hostname = row.get(hostname_field)
                if hostname:
                    display.vvv(f"Processing host: {hostname}")
                    self._add_host(hostname, row)
                else:
                    display.warning(f"Skipping row with missing hostname field: {row}")
            except Exception as e:
                error = f"Failure parsing record: {to_native(e)}"
                display.error(error)
                raise AnsibleError(error)

    def _add_host(self, hostname, host_vars):
        strict = self.get_option("strict")
        self.inventory.add_host(hostname, group="all")
        display.vvvv(f"Added host {hostname} to group 'all'")

        for var_name, var_value in host_vars.items():
            self.inventory.set_variable(hostname, var_name, var_value)
            display.vvvv(f"Set variable {var_name}={var_value} for host {hostname}")

        self._set_composite_vars(
            self.get_option("compose"), host_vars, hostname, strict=strict
        )
        self._add_host_to_composed_groups(
            self.get_option("groups"), host_vars, hostname, strict=strict
        )
        self._add_host_to_keyed_groups(
            self.get_option("keyed_groups"), host_vars, hostname, strict=strict
        )
        display.vvv(f"Completed processing for host: {hostname}")
