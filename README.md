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

# Msg Protocol

## 1. Overview

The chat application uses a custom application-level protocol built on top of **TCP**.

Messages are transmitted as **JSON objects**. Each JSON object contains a `type` field that determines how the message should be processed and a `data` field containing the message payload.

Each JSON message is terminated by a newline character (`\n`). The newline character is used as a **message delimiter**, allowing the receiver to determine where one complete message ends and the next message begins.

### General Message Format

```json
{
    "type": "<message_type>",
    "data": "<message_data>"
}\n
````

 The `\n` character is not part of the JSON object itself. It is appended to the serialized JSON message when the message is transmitted over the TCP connection.

---

 ## 2\. Message Structure

 Every message consists of two main fields:

 | Field | Type | Required | Description |
| --- | --- | --- | --- |
| `type` | `string` | Yes | Defines the type of the message and determines how it should be processed. |
| `data` | `string` | Yes | Contains the message payload as a string. |

 Example:

```
{
    "type": "broadcast",
    "data": "Hello everyone!"
}\n
```

---

 ## 3\. Message Types

 The protocol supports four message types:

 - `users` — used to communicate the list of connected users.
- `broadcast` — used to send a message to all connected users.
- `privat` — used to send a private message to a specific user.
- `command` — used to send server-side commands.

---

 ## 3.1. `users`

 The `users` message type is used to transmit information about the users currently connected to the server.

 The `data` field contains the relevant user information


 When a client receives a `users` message, it can use the contents of `data` to update the displayed list of connected users.

---

 ## 3.2. `broadcast`

 The `broadcast` message type is used to send a message to **all connected users**.

 Example:

```
{
    "type": "broadcast",
    "data": "Hello everyone!"
}\n
```

 When the server receives a `broadcast` message, it forwards the message to all currently connected clients.

---

 ## 3.3. `private`

 The `private` message type is used for **private messages** between users.

 The `data` field contains the message that should be delivered privately.

 and hear we add new field 'userName' for show server recipient

 Example:

```
{
    "type": "privat",
    "userName": "Bob"
    "data": "Hello, Bob!"
}\n
```

 The server determines the intended recipient according to the application's private-message logic and sends the message only to that user.

---

 ## 3.4. `command`

 The `command` message type is used to send **server-side commands**.

 The `data` field contains the command that should be executed by the server.

 Example:

```
{
    "type": "command",
    "data": "users"
}\n
```

 The server parses the value of `data` and performs the corresponding operation.

 ### list of commands 

 not yet

 You can also type "help" to display the help information. (not yet)

---

 ## 4\. Message Delimiting

 Because TCP provides a continuous **byte stream** rather than individual messages, the application protocol must define how the receiver determines where a message ends.

 This protocol uses the newline character (`\n`) as a message delimiter.

 For example, two messages sent consecutively are transmitted as:

```
{"type":"broadcast","data":"Hello!"}\n
{"type":"broadcast","data":"How are you?"}\n
```

 The receiver reads data from the TCP socket until it encounters `\n`. Everything before the delimiter is treated as one complete JSON message.

 The processing sequence is therefore:

 1. Read data from the TCP socket.
2. Search for the `\n` delimiter.
3. Extract the data before `\n`.
4. Parse the extracted data as JSON.
5. Read the `type` field.
6. Process the message according to its type.
7. Continue reading the TCP stream for the next message.

---

 ## 5\. Complete Message Format

 The complete wire format can be represented as:

```
JSON_OBJECT + "\n"
```

 Where the JSON object has the following structure:

```
{
    "type": "<message_type>",
    "data": "<message_data>"
}
```

 Therefore, a complete transmitted message looks like:

```
{"type":"broadcast","data":"Hello everyone!"}\n
```

 The newline character indicates the end of the current message and separates it from subsequent messages.

---

 ## 6\. Protocol Summary

 | Message Type | Purpose | `data` |
| --- | --- | --- |
| `users` | Provides the list of connected users | User list |
| `broadcast` | Sends a message to all users | Message text |
| `private` | Sends a private message | Private message text |
| `command` | Executes a server-side command | Command string |

 All messages follow the same basic structure:

```
{
    "type": "<type>",
    "data": "<data>"
}\n
```

 The `type` field determines **what the message means**, while the `data` field contains the **actual payload**. The trailing `\n` acts as the message boundary within the TCP byte stream.

```

```