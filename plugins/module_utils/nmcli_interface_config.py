from __future__ import annotations, absolute_import, division, print_function

__metaclass__ = type

import ipaddress
import json
import re
import typing


from ansible_collections.pablintino.base_infra.plugins.module_utils import (
    module_command_utils,
    nmcli_interface_exceptions,
    nmcli_interface_utils,
)

ValidateConnectionConfigurationFnType = typing.Callable[
    [
        str,
        typing.Dict[str, typing.Any],
    ],
    None,
]


class IPv4RouteConfig:
    dst: ipaddress.IPv4Network
    gw: ipaddress.IPv4Address
    metric: int = None


class IPv4Config:
    FIELD_IPV4_MODE_VAL_AUTO = "auto"
    FIELD_IPV4_MODE_VAL_DISABLED = "disabled"
    FIELD_IPV4_MODE_VAL_MANUAL = "manual"

    __FIELD_IPV4_IP = "ip"
    __FIELD_IPV4_GW = "gw"
    __FIELD_IPV4_NS = "dns"
    __FIELD_IPV4_ROUTES = "routes"
    __FIELD_IPV4_ROUTE_DST = "dst"
    __FIELD_IPV4_ROUTE_GW = "gw"
    __FIELD_IPV4_ROUTE_METRIC = "metric"

    __FIELD_IPV4_MODE = "mode"
    __FIELD_IPV4_VALS = [
        FIELD_IPV4_MODE_VAL_AUTO,
        FIELD_IPV4_MODE_VAL_MANUAL,
    ]

    def __init__(self, raw_config: typing.Dict[str, typing.Any]):
        self.__raw_config = raw_config
        self.__mode = None
        self.__ip: ipaddress.IPv4Interface = None
        self.__gw: ipaddress.IPv4Address = None
        self.__dns: typing.List[ipaddress.IPv4Address] = []
        self.__routes: typing.List[IPv4RouteConfig] = []
        self.__parse_config()

    @property
    def mode(self) -> str:
        return self.__mode

    @property
    def ip(self) -> ipaddress.IPv4Interface:
        return self.__ip

    @property
    def gw(self) -> ipaddress.IPv4Address:
        return self.__gw

    @property
    def dns(self) -> typing.List[ipaddress.IPv4Address]:
        return self.__dns

    @property
    def routes(self) -> typing.List[IPv4RouteConfig]:
        return self.__routes

    def __parse_config(self):
        if self.__FIELD_IPV4_MODE not in self.__raw_config:
            raise nmcli_interface_exceptions.NmcliInterfaceValidationException(
                f"{self.__FIELD_IPV4_MODE} is a" " mandatory field for a connection"
            )
        mode = self.__raw_config[self.__FIELD_IPV4_MODE]
        if mode not in self.__FIELD_IPV4_VALS:
            raise nmcli_interface_exceptions.NmcliInterfaceValidationException(
                f"{mode} is not a supported"
                f" {self.__FIELD_IPV4_MODE}."
                f" Supported:{', '.join(self.__FIELD_IPV4_VALS)}"
            )

        self.__mode = mode
        if self.__mode == self.FIELD_IPV4_MODE_VAL_MANUAL:
            ipv4_str = self.__raw_config.get(self.__FIELD_IPV4_IP, None)
            if not self.__FIELD_IPV4_IP:
                raise nmcli_interface_exceptions.NmcliInterfaceValidationException(
                    f"{self.__FIELD_IPV4_IP} is a mandatory field for a connection "
                    "using IPv4 static addressing"
                )

            self.__ip = nmcli_interface_utils.parse_validate_ipv4_interface_addr(
                ipv4_str
            )
            ipv4_gw_str = self.__raw_config.get(self.__FIELD_IPV4_GW, None)
            ipv4_gw = (
                nmcli_interface_utils.parse_validate_ipv4_addr(ipv4_gw_str)
                if ipv4_gw_str
                else None
            )
            if ipv4_gw and (ipv4_gw not in self.__ip.network):
                raise nmcli_interface_exceptions.NmcliInterfaceValidationException(
                    f"{self.__FIELD_IPV4_GW} is not in the {self.__ip} range"
                )
            self.__gw = ipv4_gw

        for nameserver in set(self.__raw_config.get(self.__FIELD_IPV4_NS, [])):
            self.__dns.append(
                nmcli_interface_utils.parse_validate_ipv4_addr(nameserver)
            )

        self.__parse_routes_config()

    def __parse_routes_config(self):
        routes_list = self.__raw_config.get(self.__FIELD_IPV4_ROUTES, [])
        if not isinstance(routes_list, list):
            raise nmcli_interface_exceptions.NmcliInterfaceValidationException(
                f"{self.__FIELD_IPV4_ROUTES} should be a list of IPv4 routes"
            )
        for route_data in routes_list:
            dst_str = route_data.get(self.__FIELD_IPV4_ROUTE_DST, None)
            if not dst_str:
                raise nmcli_interface_exceptions.NmcliInterfaceValidationException(
                    f"{self.__FIELD_IPV4_ROUTE_DST} is a "
                    "mandatory field for a IPv4 route"
                )
            dst_net = nmcli_interface_utils.parse_validate_ipv4_net(dst_str)
            gw_str = route_data.get(self.__FIELD_IPV4_ROUTE_GW, None)
            if not gw_str:
                raise nmcli_interface_exceptions.NmcliInterfaceValidationException(
                    f"{self.__FIELD_IPV4_ROUTE_GW} is a "
                    "mandatory field for a IPv4 route"
                )
            gw_addr = nmcli_interface_utils.parse_validate_ipv4_addr(gw_str)
            metric = route_data.get(self.__FIELD_IPV4_ROUTE_METRIC, None)
            if metric:
                try:
                    value = int(metric, 10)
                    if value < 1:
                        raise nmcli_interface_exceptions.NmcliInterfaceValidationException(
                            f"{self.__FIELD_IPV4_ROUTE_METRIC} must be a positive number"
                        )
                except ValueError as err:
                    raise nmcli_interface_exceptions.NmcliInterfaceValidationException(
                        f"{self.__FIELD_IPV4_ROUTE_METRIC} must be a number"
                    ) from err
            self.__routes.append(IPv4RouteConfig(dst_net, gw_addr, metric=metric))


class InterfaceIdentifier:
    def __init__(self, str_identifier, links_hw_addresses_cache: typing.Dict[str, str]):
        self.__str_identifier = str_identifier
        self.__links_hw_addresses_cache = links_hw_addresses_cache
        self.__str_is_mac = nmcli_interface_utils.is_mac_addr(self.__str_identifier)
        self.__iface_name = None
        self.__parse_validate()

    def __parse_validate(self):
        if not self.__str_is_mac and re.match(
            r"^[a-zA-Z0-9_\-.]*$", self.__str_identifier
        ):
            self.__iface_name = self.__str_identifier
        elif self.__str_is_mac:
            self.__iface_name = self.__resolve_from_mac()
        else:
            raise nmcli_interface_exceptions.NmcliInterfaceValidationException(
                f"{self.__str_identifier} is an invalid value for an interface identifier"
            )

    def __resolve_from_mac(self) -> str:
        result = self.__links_hw_addresses_cache.get(self.__str_identifier.lower, None)
        if not result:
            raise nmcli_interface_exceptions.NmcliInterfaceValidationException(
                f"{self.__str_identifier} cannot be resolved to an existing link"
            )
        return result

    @property
    def iface_name(self) -> str:
        return self.__iface_name


class BaseConnectionConfig:
    FIELD_STATE_VAL_UP = "up"
    FIELD_STATE_VAL_DOWN = "down"
    __FIELD_ON_STARTUP = "startup"
    _FIELD_IFACE = "iface"
    __FIELD_STATE = "state"
    __FIELD_STATE_VALUES = [
        FIELD_STATE_VAL_UP,
        FIELD_STATE_VAL_DOWN,
    ]

    def __init__(
        self,
        **kwargs,
    ):
        self._conn_name: str = kwargs["conn_name"]
        self._raw_config: typing.Dict[str, typing.Any] = kwargs["raw_config"]
        self._interface: InterfaceIdentifier = None

        self._state: str = None
        self._startup: bool = None
        self._depends_on: typing.List[str] = []
        self._related_interfaces: typing.Set[str] = set()
        self.__parse_config(kwargs["links_hw_addresses_cache"])

    @property
    def name(self) -> str:
        return self._conn_name

    @property
    def interface(self) -> InterfaceIdentifier:
        return self._interface

    @property
    def state(self) -> typing.Tuple[str, None]:
        return self._state

    @property
    def startup(self) -> typing.Tuple[bool, None]:
        return self._startup

    @property
    def depends_on(self) -> typing.List[str]:
        return self._depends_on

    @property
    def related_interfaces(self) -> typing.Set[str]:
        """
        Returns the set of interfaces that this connection uses.
        This includes the main interface associated with the connection,
        parent interfaces and children, if applicable.
        :return: The set of related connections
        """
        return self._related_interfaces

    def __parse_config(
        self,
        links_hw_addresses_cache: typing.Dict[str, str],
    ):
        # There is no real constraint about the name, but some basic
        # rules seem to be sane:
        #   - At least 4 chars
        #   - All alphanumeric except: _-.
        if not re.match(r"([a-zA-Z0-9_.-]){4,}", self._conn_name):
            raise nmcli_interface_exceptions.NmcliInterfaceValidationException(
                f"Connection name {self._conn_name} is invalid. At least alphanumeric"
                " chars are required (_-. allowed)"
            )

        startup = self._raw_config.get(self.__FIELD_ON_STARTUP, None)
        if not isinstance(startup, (bool, type(None))):
            raise nmcli_interface_exceptions.NmcliInterfaceValidationException(
                f"{self.__FIELD_ON_STARTUP} is not a proper boolean value"
            )
        self._startup = startup

        state = self._raw_config.get(self.__FIELD_STATE, None)
        if state and state not in self.__FIELD_STATE_VALUES:
            raise nmcli_interface_exceptions.NmcliInterfaceValidationException(
                f"{state} is not a supported {self.__FIELD_STATE}."
                f" Supported:{', '.join(self.__FIELD_STATE_VALUES)}"
            )
        self._state = state

        iface_str = self._raw_config.get(self._FIELD_IFACE, None)
        # Interface is always optional. Some interfaces (almost all, but specially useful
        # for someone like vpns) do create this one dynamically, and no one cares
        # about the final name of the interface
        if iface_str:
            self._interface = InterfaceIdentifier(iface_str, links_hw_addresses_cache)
            # By default, depends on the target interface. Other types may override this
            self._depends_on = [self._interface.iface_name]
            self._related_interfaces.add(self._interface.iface_name)


class MainConnectionConfig(BaseConnectionConfig):
    __FIELD_IPV4 = "ipv4"
    __FIELD_SLAVES = "slaves"

    def __init__(
        self,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self._ipv4: IPv4Config = typing.Tuple[IPv4Config, None]
        self._slaves_config: typing.List[BridgeSlaveConnectionConfig] = []
        self.__parse_config(kwargs["connection_config_factory"])

    @property
    def ipv4(self) -> typing.Tuple[IPv4Config, None]:
        return self._ipv4

    @property
    def slaves(self) -> typing.List[BridgeSlaveConnectionConfig]:
        return self._slaves_config

    def __parse_config(self, connection_config_factory: _ConnectionConfigFactory):
        ipv4_data = self._raw_config.get(self.__FIELD_IPV4, None)
        if ipv4_data:
            self._ipv4 = IPv4Config(ipv4_data)

        slave_connections = self._raw_config.get(self.__FIELD_SLAVES, {})
        if not isinstance(slave_connections, dict):
            raise nmcli_interface_exceptions.NmcliInterfaceValidationException(
                f"{self.__FIELD_SLAVES} should be a dict of slave connections"
            )

        for conn_name, raw_config in slave_connections.items():
            slave_config = connection_config_factory.build_slave_connection(
                conn_name, raw_config, self
            )
            self._slaves_config.append(slave_config)
            # Add child connection's interfaces as related to the main connection
            self._related_interfaces.update(slave_config.related_interfaces)


class SlaveConnectionConfig(BaseConnectionConfig):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._main_connection_config: MainConnectionConfig = kwargs[
            "main_connection_config"
        ]

    @property
    def main_connection_config(self) -> MainConnectionConfig:
        return self._main_connection_config


class EthernetConnectionConfig(MainConnectionConfig):
    pass


class VlanConnectionConfigMixin(BaseConnectionConfig):
    __FIELD_VLAN = "vlan"
    __FIELD_VLAN_ID = "id"
    __FIELD_VLAN_PARENT_IFACE = "parent"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._vlan_id: int = None
        self._parent_interface: InterfaceIdentifier = None
        self.__parse_config(kwargs["links_hw_addresses_cache"])

    @property
    def parent_interface(self) -> InterfaceIdentifier:
        return self._parent_interface

    @property
    def vlan_id(self) -> int:
        return self._vlan_id

    def __parse_config(
        self,
        links_hw_addresses_cache: typing.Dict[str, str],
    ):
        vlan_config = self._raw_config.get(self.__FIELD_VLAN, None)
        if not vlan_config:
            raise nmcli_interface_exceptions.NmcliInterfaceValidationException(
                f"{self.__FIELD_VLAN} is a mandatory field for a VLAN based connection"
            )

        vlan_parent_iface = vlan_config.get(self.__FIELD_VLAN_PARENT_IFACE, None)
        if not vlan_parent_iface:
            raise nmcli_interface_exceptions.NmcliInterfaceValidationException(
                f"{self.__FIELD_VLAN_PARENT_IFACE} is a mandatory"
                f" field of {self.__FIELD_VLAN} section for a VLAN based connection"
            )

        self._parent_interface = InterfaceIdentifier(
            vlan_parent_iface, links_hw_addresses_cache
        )

        # VLANs dependency is not the interface name, it's the parent iface
        self._depends_on = [self._parent_interface.iface_name]

        # Add to the related interfaces the parent too. VLAN interfaces relate
        # to the interface created for the VLAN and to the parent one
        self._related_interfaces.add(self._parent_interface.iface_name)

        if (
            self.interface
            and self._parent_interface.iface_name == self.interface.iface_name
        ):
            raise nmcli_interface_exceptions.NmcliInterfaceValidationException(
                f"{self.__FIELD_VLAN_PARENT_IFACE} field of "
                f"{self.__FIELD_VLAN} cannot point to the same interface told by "
                f"{self._FIELD_IFACE} ({self.interface.iface_name})"
            )

        vlan_id = vlan_config.get(self.__FIELD_VLAN_ID, None)
        if not vlan_id:
            raise nmcli_interface_exceptions.NmcliInterfaceValidationException(
                f"{self.__FIELD_VLAN_ID} is a mandatory field of {self.__FIELD_VLAN} "
                "section for a VLAN based connection"
            )
        if not isinstance(vlan_id, int):
            raise nmcli_interface_exceptions.NmcliInterfaceValidationException(
                f"{self.__FIELD_VLAN_ID}  field of {self.__FIELD_VLAN} section must be a number"
            )

        if vlan_id <= 0:
            raise nmcli_interface_exceptions.NmcliInterfaceValidationException(
                f"{self.__FIELD_VLAN_ID} field of {self.__FIELD_VLAN} "
                "section must be greater than zero"
            )
        self._vlan_id = vlan_id


class VlanConnectionConfig(MainConnectionConfig, VlanConnectionConfigMixin):
    pass


class BridgeSlaveConnectionConfig(SlaveConnectionConfig):
    pass


class EthernetSlaveConnectionConfig(SlaveConnectionConfig):
    pass


class VlanSlaveConnectionConfig(SlaveConnectionConfig, VlanConnectionConfigMixin):
    pass


class BridgeConnectionConfig(MainConnectionConfig):
    pass


class _ConnectionConfigFactory:
    __FIELD_TYPE = "type"
    __FIELD_TYPE_VAL_ETHERNET = "ethernet"
    __FIELD_TYPE_VAL_VLAN = "vlan"
    __FIELD_TYPE_VAL_BRIDGE = "bridge"

    __SLAVES_CONFIG_TYPES_MAP = {
        __FIELD_TYPE_VAL_ETHERNET: EthernetSlaveConnectionConfig,
        __FIELD_TYPE_VAL_VLAN: VlanSlaveConnectionConfig,
    }

    __CONFIG_TYPES_MAP = {
        __FIELD_TYPE_VAL_ETHERNET: EthernetConnectionConfig,
        __FIELD_TYPE_VAL_VLAN: VlanConnectionConfig,
        __FIELD_TYPE_VAL_BRIDGE: BridgeConnectionConfig,
    }

    def __init__(self, links_hw_addresses: typing.Dict[str, str]):
        self.__links_hw_addresses = links_hw_addresses

    def build_slave_connection(
        self,
        conn_name: str,
        conn_config: typing.Dict[str, typing.Any],
        main_connection_config: MainConnectionConfig,
    ) -> SlaveConnectionConfig:
        conn_type = conn_config.get(self.__FIELD_TYPE, None)
        if not conn_type:
            raise nmcli_interface_exceptions.NmcliInterfaceValidationException(
                f"{self.__FIELD_TYPE} is a mandatory field for a slave connection"
            )

        if conn_type not in self.__SLAVES_CONFIG_TYPES_MAP:
            raise nmcli_interface_exceptions.NmcliInterfaceValidationException(
                f"Unsupported slave connection type {conn_type} for connection {conn_name}"
            )

        return self.__SLAVES_CONFIG_TYPES_MAP[conn_type](
            conn_name=conn_name,
            raw_config=conn_config,
            links_hw_addresses_cache=self.__links_hw_addresses,
            main_connection_config=main_connection_config,
        )

    def build_connection(
        self, conn_name: str, conn_config: typing.Dict[str, typing.Any]
    ) -> MainConnectionConfig:
        conn_type = conn_config.get(self.__FIELD_TYPE, None)
        if not conn_type:
            raise nmcli_interface_exceptions.NmcliInterfaceValidationException(
                f"{self.__FIELD_TYPE} is a mandatory field for a connection"
            )

        if conn_type not in self.__CONFIG_TYPES_MAP:
            raise nmcli_interface_exceptions.NmcliInterfaceValidationException(
                f"Unsupported connection type {conn_type} for connection {conn_name}"
            )

        return self.__CONFIG_TYPES_MAP[conn_type](
            conn_name=conn_name,
            raw_config=conn_config,
            links_hw_addresses_cache=self.__links_hw_addresses,
            connection_config_factory=self,
        )

        return config


class ConnectionsConfigurationHandler:
    def __init__(
        self,
        raw_config: typing.Dict[str, typing.Any],
        runner_fn: module_command_utils.CommandRunnerFn,
    ):
        self.__raw_config = raw_config
        self.__runner_fn = runner_fn
        self.__conn_configs: typing.List[MainConnectionConfig] = []
        self.__links_hw_addresses = self.__fetch_links_hw_addresses()
        self.__connection_config_factory = _ConnectionConfigFactory(
            self.__links_hw_addresses
        )

    def __fetch_links_hw_addresses(self) -> typing.Dict[str, str]:
        result = self.__runner_fn(["ip", "-br", "-j", "link"], check=True)
        links_hw_addresses = {}
        for link_data in json.loads(result.stdout):
            if_name = link_data.get("ifname", None)
            address = link_data.get("address", None)
            if if_name and address and (if_name not in links_hw_addresses):
                links_hw_addresses[address.lower()] = if_name

        return links_hw_addresses

    def parse(self):
        if not isinstance(self.__raw_config, dict):
            raise nmcli_interface_exceptions.NmcliInterfaceValidationException(
                "The provided configuration is not a dictionary of connections"
            )

        mapped_connections = {
            conn_name: self.__connection_config_factory.build_connection(
                conn_name, conn_data
            )
            for conn_name, conn_data in self.__raw_config.items()
        }
        self.__conn_configs = self.__sort_connections(mapped_connections)

    @property
    def connections(self) -> typing.List[MainConnectionConfig]:
        # Return a copy of the list itself
        return self.__conn_configs[:]

    @classmethod
    def __sort_conn_ifaces(
        cls, interfaces_dependencies_graph, graph_iface, visited, ifaces_stack
    ):
        visited.append(graph_iface)

        for element in interfaces_dependencies_graph[graph_iface]:
            if graph_iface not in visited:
                cls.__sort_conn_ifaces(
                    interfaces_dependencies_graph, element, visited, ifaces_stack
                )
        ifaces_stack.insert(0, graph_iface)

    @classmethod
    def __sort_connections(cls, conn_configs: typing.List[MainConnectionConfig]):
        # Prepare the dependency graph
        interfaces_dependencies_graph = {}
        graph_ifaces_set = set()
        ifaces_to_conn_dict: typing.Dict[str, MainConnectionConfig] = {}

        # The interface field is the one used for computing dependency
        # It's not mandatory and, if not provided, that connection
        # cannot be used as a dependency, which is fine.
        non_iface_connections = []
        for conn_config in conn_configs.values():
            # All connections that have no interface field are created at the
            # very end. The shorting algorithm doesn't apply to them
            if not conn_config.interface:
                non_iface_connections.append(conn_config)
                continue

            # If the connection points to itself is not a dependency to other conn.
            # It's safe to treat it as is an external provisioned one or like a connection
            # that doesn't support dependencies like ethernet or wi-fi
            ifname = conn_config.interface.iface_name
            if ifname not in interfaces_dependencies_graph:
                interfaces_dependencies_graph[ifname] = []

            if [ifname] != conn_config.depends_on:
                interfaces_dependencies_graph[ifname].extend(conn_config.depends_on)
                # This default to empty list is important, as interfaces like VLANs
                # may reference a parent interface that is not part of this configuration
                # because is managed outside
                for iface_dependency in conn_config.depends_on:
                    # Init the dependency to an empty list meaning it doesn't depend on anything
                    if iface_dependency not in interfaces_dependencies_graph:
                        interfaces_dependencies_graph[iface_dependency] = []

                # As to apply the shorting algorithm, we need to know the
                # list of elements to sort so, we save all the involved interfaces in a set
                graph_ifaces_set.update(conn_config.depends_on)

            graph_ifaces_set.add(ifname)
            ifaces_to_conn_dict[ifname] = conn_config

        visited = []
        ifaces_stack = []
        for graph_iface in graph_ifaces_set:
            if graph_iface not in visited:
                cls.__sort_conn_ifaces(
                    interfaces_dependencies_graph,
                    graph_iface,
                    visited,
                    ifaces_stack,
                )

        sorted_conn_configs = [
            ifaces_to_conn_dict[iface_name]
            for iface_name in ifaces_stack
            if iface_name in ifaces_to_conn_dict
        ]

        # Append interfaces/connections that doesn't need sorting
        # at the end of the list. Those will be the last ones
        # to be configured
        sorted_conn_configs.extend(non_iface_connections)
        return sorted_conn_configs