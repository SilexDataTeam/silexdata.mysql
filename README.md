<!--
Copyright (c) Silex Data Team
Licensed under the Apache License, Version 2.0 (see LICENSE or https://www.apache.org/licenses/LICENSE-2.0)
SPDX-License-Identifier: Apache-2.0
-->

# Silex Data MySQL Collection

This repository contains the `silexdata.mysql` Ansible Collection. The collection provides modules and plugins for managing MySQL databases, users, privileges, and related resources with Ansible.

## Code of Conduct

We follow [Ansible Code of Conduct](https://docs.ansible.com/ansible/latest/community/code_of_conduct.html) in all our interactions within this project.

If you encounter abusive behavior violating the [Ansible Code of Conduct](https://docs.ansible.com/ansible/latest/community/code_of_conduct.html), please refer to the [policy violations](https://docs.ansible.com/ansible/latest/community/code_of_conduct.html#policy-violations) section of the Code of Conduct for information on how to raise a complaint.

## External requirements

Some modules and plugins require external libraries. Please check the requirements for each plugin or module you use in the documentation to find out which requirements are needed.

## Included content

Please check the included content on the [Ansible Galaxy page for this collection](https://galaxy.ansible.com/ui/repo/published/silexdata/mysql/).

## Using this collection

You must install this collection from [Ansible Galaxy](https://galaxy.ansible.com/ui/repo/published/silexdata/mysql/) using the `ansible-galaxy` command-line tool, regardless of your Ansible installation type:

    ansible-galaxy collection install silexdata.mysql

You can also include it in a `requirements.yml` file and install it via `ansible-galaxy collection install -r requirements.yml` using the format:

```yaml
collections:
- name: silexdata.mysql
```

Note that if you install the collection manually, it will not be upgraded automatically. To upgrade the collection to the latest available version, run the following command:

```bash
ansible-galaxy collection install silexdata.mysql --upgrade
```

You can also install a specific version of the collection, for example, if you need to downgrade when something is broken in the latest version (please report an issue in this repository). Use the following syntax where `X.Y.Z` can be any [available version](https://galaxy.ansible.com/ui/repo/published/silexdata/mysql/):

```bash
ansible-galaxy collection install silexdata.mysql:==X.Y.Z
```

See [Ansible Using collections](https://docs.ansible.com/ansible/latest/user_guide/collections_using.html) for more details.

## Contributing to this collection

All types of contributions are very welcome.

You can find more information in the [developer guide for collections](https://docs.ansible.com/ansible/devel/dev_guide/developing_collections.html#contributing-to-collections), and in the [Ansible Community Guide](https://docs.ansible.com/ansible/latest/community/index.html).

### Running tests

See [here](https://docs.ansible.com/ansible/devel/dev_guide/developing_collections.html#testing-collections).

## Collection maintenance

To learn how to maintain / become a maintainer of this collection, refer to:

* [Maintainer guidelines](https://github.com/ansible/community-docs/blob/main/maintaining.rst).

It is necessary for maintainers of this collection to be subscribed to:

* The collection itself (the `Watch` button → `All Activity` in the upper right corner of the repository's homepage).

## Publishing New Version

See the [Releasing guidelines](https://github.com/ansible/community-docs/blob/main/releasing_collections.rst) to learn how to release this collection.

## Release notes

See the [changelog](https://github.com/SilexDataTeam/silexdata.mysql/blob/main/CHANGELOG.md).

## More information

- [Ansible Collection overview](https://github.com/ansible-collections/overview)
- [Ansible User guide](https://docs.ansible.com/ansible/latest/user_guide/index.html)
- [Ansible Developer guide](https://docs.ansible.com/ansible/latest/dev_guide/index.html)
- [Ansible Community code of conduct](https://docs.ansible.com/ansible/latest/community/code_of_conduct.html)

## Licensing

This collection is licensed under the Apache License, Version 2.0.

See the [LICENSE](LICENSE) file in this repository or visit the official license page: https://www.apache.org/licenses/LICENSE-2.0

You are free to use, modify, and distribute this collection under the terms of the Apache 2.0 license. Contributions to this project will also be licensed under Apache 2.0 unless otherwise noted.
