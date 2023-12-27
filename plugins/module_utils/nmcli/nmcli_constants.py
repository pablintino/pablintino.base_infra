from __future__ import absolute_import, division, print_function

__metaclass__ = type

import typing
import uuid

from ansible_collections.pablintino.base_infra.plugins.module_utils.net import (
    net_config,
)

# NMCLI Connection General section fields
NMCLI_CONN_FIELD_GENERAL_NAME = "general.name"
NMCLI_CONN_FIELD_GENERAL_STATE = "general.state"
NMCLI_CONN_FIELD_GENERAL_STATE_VAL_ACTIVATED = "activated"
NMCLI_CONN_FIELD_GENERAL_UUID = "general.uuid"
NMCLI_CONN_FIELD_GENERAL_DEVICES = "general.devices"

# NMCLI Connection section fields
NMCLI_CONN_FIELD_CONNECTION_ID = "connection.id"
NMCLI_CONN_FIELD_CONNECTION_UUID = "connection.uuid"
NMCLI_CONN_FIELD_CONNECTION_STATE = "connection.state"
NMCLI_CONN_FIELD_CONNECTION_MASTER = "connection.master"
NMCLI_CONN_FIELD_CONNECTION_SLAVE_TYPE = "connection.slave-type"
NMCLI_CONN_FIELD_CONNECTION_AUTOCONNECT = "connection.autoconnect"
NMCLI_CONN_FIELD_CONNECTION_INTERFACE_NAME = "connection.interface-name"
NMCLI_CONN_FIELD_CONNECTION_TYPE = "connection.type"
NMCLI_CONN_FIELD_CONNECTION_TYPE_VAL_ETHERNET = "802-3-ethernet"
NMCLI_CONN_FIELD_CONNECTION_TYPE_VAL_VLAN = "vlan"
NMCLI_CONN_FIELD_CONNECTION_TYPE_VAL_BRIDGE = "bridge"
NMCLI_CONN_FIELD_CONNECTION_TYPE_VAL_BOND = "bond"

# NMCLI Connection IP4 section fields (IP4, not IPv4)
# This section is read-only
NMCLI_CONN_FIELD_IP4_ADDRESS = "ip4.address"

# NMCLI Connection IP6 section fields (IP6, not IPv6)
# This section is read-only
NMCLI_CONN_FIELD_IP6_ADDRESS = "ip6.address"

# NMCLI Connection IP section constants
__NMCLI_CONN_FIELD_PREFIX_IPV4 = "ipv4"
__NMCLI_CONN_FIELD_PREFIX_IPV6 = "ipv6"
__NMCLI_CONN_FIELD_SUFFIX_METHOD = ".method"
__NMCLI_CONN_FIELD_SUFFIX_ADDRESSES = ".addresses"
__NMCLI_CONN_FIELD_SUFFIX_GATEWAY = ".gateway"
__NMCLI_CONN_FIELD_SUFFIX_DNS = ".dns"
__NMCLI_CONN_FIELD_SUFFIX_ROUTES = ".routes"
__NMCLI_CONN_FIELD_SUFFIX_NEVER_DEFAULT = ".never-default"
__IP_VERSION_4 = 4
__IP_VERSION_6 = 6
NMCLI_CONN_FIELD_IP_METHOD = {
    __IP_VERSION_4: __NMCLI_CONN_FIELD_PREFIX_IPV4 + __NMCLI_CONN_FIELD_SUFFIX_METHOD,
    __IP_VERSION_6: __NMCLI_CONN_FIELD_PREFIX_IPV6 + __NMCLI_CONN_FIELD_SUFFIX_METHOD,
}
NMCLI_CONN_FIELD_IP_ADDRESSES = {
    __IP_VERSION_4: __NMCLI_CONN_FIELD_PREFIX_IPV4 + __NMCLI_CONN_FIELD_SUFFIX_ADDRESSES,
    __IP_VERSION_6: __NMCLI_CONN_FIELD_PREFIX_IPV6 + __NMCLI_CONN_FIELD_SUFFIX_ADDRESSES,
}
NMCLI_CONN_FIELD_IP_GATEWAY = {
    __IP_VERSION_4: __NMCLI_CONN_FIELD_PREFIX_IPV4 + __NMCLI_CONN_FIELD_SUFFIX_GATEWAY,
    __IP_VERSION_6: __NMCLI_CONN_FIELD_PREFIX_IPV6 + __NMCLI_CONN_FIELD_SUFFIX_GATEWAY,
}
NMCLI_CONN_FIELD_IP_DNS = {
    __IP_VERSION_4: __NMCLI_CONN_FIELD_PREFIX_IPV4 + __NMCLI_CONN_FIELD_SUFFIX_DNS,
    __IP_VERSION_6: __NMCLI_CONN_FIELD_PREFIX_IPV6 + __NMCLI_CONN_FIELD_SUFFIX_DNS,
}
NMCLI_CONN_FIELD_IP_ROUTES = {
    __IP_VERSION_4: __NMCLI_CONN_FIELD_PREFIX_IPV4 + __NMCLI_CONN_FIELD_SUFFIX_ROUTES,
    __IP_VERSION_6: __NMCLI_CONN_FIELD_PREFIX_IPV6 + __NMCLI_CONN_FIELD_SUFFIX_ROUTES,
}
NMCLI_CONN_FIELD_IP_NEVER_DEFAULT = {
    __IP_VERSION_4: __NMCLI_CONN_FIELD_PREFIX_IPV4 + __NMCLI_CONN_FIELD_SUFFIX_NEVER_DEFAULT,
    __IP_VERSION_6: __NMCLI_CONN_FIELD_PREFIX_IPV6 + __NMCLI_CONN_FIELD_SUFFIX_NEVER_DEFAULT,
}
NMCLI_CONN_FIELD_IP_METHOD_VAL_AUTO = "auto"
NMCLI_CONN_FIELD_IP_METHOD_VAL_MANUAL = "manual"
NMCLI_CONN_FIELD_IP_METHOD_VAL_DISABLED = "disabled"

# NMCLI Connection VLAN section fields
NMCLI_CONN_FIELD_VLAN_VLAN_ID = "vlan.id"
NMCLI_CONN_FIELD_VLAN_VLAN_PARENT = "vlan.parent"

NMCLI_DEVICE_ETHERNET_MTU_FIELD = "general.mtu"
NMCLI_DEVICE_ETHERNET_MAC_FIELD = "general.hwaddr"
NMCLI_DEVICE_CONNECTION_NAME = "general.connection"

__NMCLI_TYPE_CONVERSION_TABLE = {
    net_config.EthernetConnectionConfig: NMCLI_CONN_FIELD_CONNECTION_TYPE_VAL_ETHERNET,
    net_config.VlanConnectionConfig: NMCLI_CONN_FIELD_CONNECTION_TYPE_VAL_VLAN,
    net_config.BridgeConnectionConfig: NMCLI_CONN_FIELD_CONNECTION_TYPE_VAL_BRIDGE,
    net_config.EthernetSlaveConnectionConfig: NMCLI_CONN_FIELD_CONNECTION_TYPE_VAL_ETHERNET,
    net_config.VlanSlaveConnectionConfig: NMCLI_CONN_FIELD_CONNECTION_TYPE_VAL_VLAN,
}

__NMCLI_IP_METHOD_CONVERSION_TABLE = {
    net_config.IPConfig.FIELD_IP_MODE_VAL_AUTO: NMCLI_CONN_FIELD_IP_METHOD_VAL_AUTO,
    net_config.IPConfig.FIELD_IP_MODE_VAL_MANUAL: NMCLI_CONN_FIELD_IP_METHOD_VAL_MANUAL,
    net_config.IPConfig.FIELD_IP_MODE_VAL_DISABLED: NMCLI_CONN_FIELD_IP_METHOD_VAL_DISABLED,
}


def map_config_to_nmcli_type_field(
        config: net_config.BaseConnectionConfig,
) -> str:
    nmcli_conn_type = __NMCLI_TYPE_CONVERSION_TABLE.get(type(config), None)
    if nmcli_conn_type:
        return nmcli_conn_type
    raise ValueError(f"Unsupported config type {type(config)}")


def map_config_ip_method_to_nmcli_ip_method_field(
        config_ip_method: str,
) -> str:
    nmcli_conn_method = __NMCLI_IP_METHOD_CONVERSION_TABLE.get(
        config_ip_method, None
    )
    if nmcli_conn_method:
        return nmcli_conn_method
    raise ValueError(f"Unsupported IP method {config_ip_method}")


def is_connection_master_of(
        slave_conn_data: typing.Dict[str, typing.Any],
        master_conn_data: typing.Dict[str, typing.Any],
) -> bool:
    """
    Checks if a given master connection is the master of the given slave.
    This check takes into account that that link can be done by using
    the UUID or the master interface name to relate both connections.
    :param slave_conn_data: A dict that holds all the parameters of the slave connection.
    :param master_conn_data: A dict that holds all the parameters of the slave connection.
    :return: True if the given slave has the given master connection as master. False otherwise.
    """
    conn_master_id = slave_conn_data[NMCLI_CONN_FIELD_CONNECTION_MASTER]
    compare_field = NMCLI_CONN_FIELD_CONNECTION_UUID
    try:
        uuid.UUID(conn_master_id)
    except ValueError:
        compare_field = NMCLI_CONN_FIELD_CONNECTION_INTERFACE_NAME

    return conn_master_id == master_conn_data.get(compare_field, None)
