<!--
SPDX-FileCopyrightText: Silex Data Solutions
SPDX-License-Identifier: Apache-2.0
-->

# setup_mysql integration target

This is the setup role every `<module_name>` integration target in this
collection should declare as a `meta/main.yml` dependency (see the
`inventory/` target). It is responsible for:

1. Initializing the shared `setup_mysql_*` variables
   (credentials/endpoint placeholders, using the `.invalid` TLD so a dry run
   reliably reports the service as unavailable).
2. Probing whether the real service is reachable and recording the result in
   a `setup_mysql_service_available` fact.
3. Either failing the run (if `setup_mysql_require_service` is
   `true`) or emitting a warning containing the `SETUP_SERVICE_UNAVAILABLE`
   marker token (if not) when the service is unreachable.

## Why gate on service availability at all

This lets the full test suite — including live, service-dependent assertions
— run in CI without real credentials: argument-validation and check-mode
tests always run, while live tests are automatically skipped (with a visible
warning) when there is nothing to talk to. Pipelines that must have live
coverage set `setup_mysql_require_service: true` (e.g. via
`tests/integration/integration_config.yml`, see
`tests/integration/integration_config.yml.template`) to turn that warning into
a hard failure instead.

## Credentials

`defaults/main.yml` holds dry-run placeholders: `setup_mysql_db_host`,
`setup_mysql_db_port`, `setup_mysql_db_user`, `setup_mysql_db_password` and
`setup_mysql_db_name`. Override them in `tests/integration/integration_config.yml`,
or through the environment variables `antsibull-nox.toml` maps to them, to run
the live tests. Those only run `SELECT` statements over literal values, so any
database the user may connect to will do. The probe logs in with `pymysql`, so
a rejected login counts as the service being unavailable.
