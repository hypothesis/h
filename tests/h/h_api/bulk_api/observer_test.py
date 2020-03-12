import json
from io import StringIO

from h.h_api.bulk_api.observer import SerialisingObserver
from h.h_api.enums import CommandStatus


class TestSerialisingObserver:
    def test_it_only_serialises_commands_as_received(self, user_command, group_command):
        handle = StringIO()
        observer = SerialisingObserver(handle)

        observer.observe_command(user_command, CommandStatus.AS_RECEIVED)
        observer.observe_command(group_command, CommandStatus.AS_RECEIVED)
        observer.observe_command(group_command, CommandStatus.POST_EXECUTE)

        data = [json.loads(line) for line in handle.getvalue().strip().split("\n")]

        assert data == [user_command.raw, group_command.raw]
