# -*- coding: utf-8 -*-
# cython: language_level=3
# Copyright (c) 2021-present VincentRPS

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE

import asyncio
import inspect
from collections import OrderedDict
from typing import Any, Callable, Optional

from ...internal import run_storage
from ...message import Message
from ...state import ConnectionState
from .context import Context
from ...channels import TextChannel, VoiceChannel
from ...member import Member
from ...user import User


def resolve_id(string: str) -> int:
    ret = string[2:-1]
    return ret


class Command:
    """Represents a prefixed Discord command

    .. versionadded:: 0.9.0
    """

    def __init__(
        self,
        func: Callable,
        name: str,
        prefix: str,
        state: ConnectionState,
        *,
        cog = None,
        description: Optional[str] = None
    ):
        if not asyncio.iscoroutinefunction(func):
            raise TypeError("Command must be a coroutine")
        self.name = name
        self.coro = func
        self.prefix = prefix
        self.state = state
        self.cog = cog
        self._desc = description or func.__doc__ or "No description provided"
        self._storage = run_storage.InternalRunner(self.state.loop)

    @property
    def options(self):
        dict = OrderedDict(inspect.signature(self._callback).parameters)
        dict.popitem(last=False)
        return dict

    @property
    def _callback(self):
        return self.coro

    @_callback.setter
    def _callback(self, func: Callable[..., Any]):
        self.coro = func

    def _run(self, context, *args, **kwargs):
        if self.cog:
            self.state.loop.create_task(
                self._storage._run_process(
                    self.coro, self.cog, context, *args, **kwargs
                )
            )
        else:
            self.state.loop.create_task(
                self._storage._run_process(self.coro, context, *args, **kwargs)
            )

    def _run_with_options_detected(self, context: Context):
        order = 0
        to_give = OrderedDict()
        for name, param in self.options.items():
            order += 1
            if param.annotation == str:
                give = self.content_without_command.split(" ")[order]
                to_give[name] = give
            
            elif param.annotation == TextChannel:
                id = resolve_id(self.content_without_command.split(" ")[order])
                raw = self.state.channels.get(id)
                give = TextChannel(raw, self.state)
                to_give[name] = give
            
            elif param.annotation == VoiceChannel:
                id = resolve_id(self.content_without_command.split(" ")[order])
                raw = self.state.channels.get(id)
                give = VoiceChannel(raw, self.state)
                to_give[name] = give
            
            elif param.annotation == Member or param.annotation == User:
                id = resolve_id(self.content_without_command.split(" ")[order])
                raw = self.state.members.get(id)
                give = Member(raw, context.message.guild.id, context.message.app.factory)
                to_give[name] = give
            
            else:
                give = self.content_without_command.split(" ")[order]
                to_give[name] = give

        self._run(context, **to_give)

    def invoke(self, msg: Message, **kwargs):
        if "content" in kwargs:
            self.content_without_command: str = kwargs.get("content")
        context = Context(msg, self)
        self._run_with_options_detected(context)
