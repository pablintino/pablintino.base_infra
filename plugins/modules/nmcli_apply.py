#!/usr/bin/env python3

from __future__ import absolute_import, division, print_function

__metaclass__ = type

from ansible.module_utils.basic import AnsibleModule


from ansible_collections.pablintino.base_infra.plugins.module_utils.module_command_utils import (
    get_module_command_runner,
)

from ansible_collections.pablintino.base_infra.plugins.module_utils.nmcli_interface_exceptions import (
    NmcliInterfaceException,
)

from ansible_collections.pablintino.base_infra.plugins.module_utils.nmcli_querier import (
    NetworkManagerQuerier,
)

from ansible_collections.pablintino.base_infra.plugins.module_utils.nmcli_interface import (
    NetworkManagerConfiguratorFactory,
)

from ansible_collections.pablintino.base_infra.plugins.module_utils.nmcli_interface_args_builders import (
    nmcli_args_builder_factory,
)

from ansible_collections.pablintino.base_infra.plugins.module_utils.nmcli_interface_config import (
    ConnectionsConfigurationHandler,
)


def __parse_get_connections(module):
    connections = module.params.get("connections", {})
    if not isinstance(connections, dict):
        module.fail_json(msg="connections must a dictionary")

    return connections


def main():
    module = AnsibleModule(
        argument_spec={
            "connections": {"type": "raw", "required": True},
        },
        supports_check_mode=False,
    )

    module.run_command_environ_update = {
        "LANG": "C",
        "LC_ALL": "C",
        "LC_MESSAGES": "C",
        "LC_CTYPE": "C",
    }

    result = {
        "changed": False,
        "success": False,
    }

    try:
        command_runner = get_module_command_runner(module)
        nmcli_querier = NetworkManagerQuerier(command_runner)

        nmcli_factory = NetworkManagerConfiguratorFactory(
            command_runner,
            nmcli_querier,
            nmcli_args_builder_factory,
        )

        config_handler = ConnectionsConfigurationHandler(
            __parse_get_connections(module), command_runner
        )

        #import pydevd_pycharm

        #pydevd_pycharm.settrace(
        #    "localhost", port=5555, stdoutToServer=True, stderrToServer=True
        #)
        config_handler.parse()
        conn_result = {}
        for conn_config in config_handler.connections:
            conn_config_result = nmcli_factory.build_configurator(
                conn_config
            ).configure(conn_config)
            conn_result[conn_config.name] = conn_config_result.to_dict()
            result["changed"] = result["changed"] or conn_config_result.changed

        result["success"] = True
        result["result"] = conn_result
        module.exit_json(**result)
    except NmcliInterfaceException as err:
        result.update(err.to_dict())
        module.fail_json(**result)


if __name__ == "__main__":
    main()