from __future__ import absolute_import, division, print_function

__metaclass__ = type

import typing

from ansible_collections.pablintino.base_infra.plugins.module_utils import (
    encoding,
)


class BaseInfraException(Exception):
    def __init__(
        self,
        msg: str,
    ) -> None:
        super().__init__()
        self.msg = msg

    def to_dict(self) -> typing.Dict[str, typing.Any]:
        return encoding.to_basic_types(
            self.__dict__.items(), filter_private_fields=True
        )


class ValueInfraException(BaseInfraException):
    def __init__(
        self,
        msg: str,
        field: str = None,
        value: typing.Any = None,
    ) -> None:
        super().__init__(msg)
        self.field = field
        self.value = value