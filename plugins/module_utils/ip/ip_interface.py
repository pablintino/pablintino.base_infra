from __future__ import absolute_import, division, print_function

__metaclass__ = type


import json
import typing

from ansible_collections.pbtn.common.plugins.module_utils import (
    module_command_utils,
)


class IPAddrData(dict):
    ADDR_DETAILS_IFNAME = "ifname"
    ADDR_DETAILS_LINK = "link"
    ADDR_DETAILS_ADDR_INFO = "addr_info"
    ADDR_DETAILS_ADDR_INFO_LOCAL_IP = "local"

    @property
    def if_name(self) -> str:
        return self.get(self.ADDR_DETAILS_IFNAME, None)

    @property
    def link(self) -> str:
        return self.get(self.ADDR_DETAILS_LINK, None)

    @property
    def addr_info(self) -> typing.List[typing.Dict[str, typing.Any]]:
        return self.get(self.ADDR_DETAILS_ADDR_INFO, None)


class IPLinkData(dict):
    LINK_DETAILS_IFNAME = "ifname"
    LINK_DETAILS_LINK = "link"
    LINK_DETAILS_ADDR = "address"
    LINK_DETAILS_LINK_INFO = "linkinfo"
    LINK_DETAILS_INFO_KIND = "info_kind"

    @property
    def if_name(self) -> str:
        return self.get(self.LINK_DETAILS_IFNAME, None)

    @property
    def link(self) -> str:
        return self.get(self.LINK_DETAILS_LINK, None)

    @property
    def address(self) -> str:
        addr = self.get(self.LINK_DETAILS_ADDR, None)
        return addr.lower() if addr else addr

    @property
    def link_kind(self) -> str:
        return self.get(self.LINK_DETAILS_LINK_INFO, {}).get(
            self.LINK_DETAILS_INFO_KIND, None
        )


class IPInterface:
    __FETCH_LINKS_CMD = ["ip", "-detail", "-j", "link"]

    def __init__(self, runner_fn: module_command_utils.CommandRunnerFn):
        self.__runner_fn = runner_fn

    def get_ip_links(self) -> typing.List[IPLinkData]:
        return [
            IPLinkData(data)
            for data in json.loads(
                self.__runner_fn(self.__FETCH_LINKS_CMD, check=True).stdout
            )
        ]
