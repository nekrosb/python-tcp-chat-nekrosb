# python-tcp-chat-nekrosb

### what it is

this small Project Python TCP chat with the possibility Brodcast messages and private messages

### requirements

- python 3.13+
- uv 

### run project

'''bash 
uv sync

# for run the server
uv run src/server.py

# for run the client.py 
uv run src/client.py
'''

# Message Protocol

The chat uses newline-delimited JSON over TCP. Every transmitted message is one
JSON object followed by `\n`:

```json
{"type": "broadcast", "data": "Hello everyone!"}\n
```

The newline is a transport delimiter, not part of the JSON object. Because TCP
is a byte stream, the receiver may read several messages at once or only part
of one message. The client and server buffer bytes and process each complete
line separately.

## Message fields

| Field | Required | Description |
| --- | --- | --- |
| `type` | yes | Determines how the message is handled. |
| `data` | yes | The message payload. It is text for chat messages and an object for `users` responses. |
| `command` | no | Server command name: `changeNickname` or `private`. |
| `userName` | no | Recipient nickname for private messages. |

The server sends the complete JSON envelope, but the client displays only the
`data` field. The `type`, `command`, and `userName` fields are protocol metadata
and are not shown as chat text.

## Message types

### `broadcast`

Client to server:

```json
{"type": "broadcast", "data": "Hello everyone!"}\n
```

The server forwards the text in `data` to the other connected users.

### `users`

Client request:

```json
{"type": "users", "data": ""}\n
```

Server response:

```json
{"type": "users", "data": {"alice": "127.0.0.1:5001"}}\n
```

The client renders the `data` object as a users table.

### `command`

Commands use `command` for the operation name and `data` for its argument:

```json
{"type": "command", "command": "changeNickname", "data": "new_name"}\n
```

The currently supported server command is `changeNickname`.

Private message command:

```text
/private <nickname> <message>
```

It is sent as a `command` message with `command: "private"`, the recipient in
`userName`, and the message text in `data`.

## Current limitations

Private messages are delivered only to users currently connected to the chat.