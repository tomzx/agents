# Interaction Diagrams Reference

Sequence and ZenUML diagrams show how actors exchange messages over time.

## Sequence Diagrams (`sequenceDiagram`)

```
sequenceDiagram
    autonumber
    actor U as User
    participant API
    participant DB as Database

    U->>API: POST /login
    activate API
    API->>DB: query credentials
    DB-->>API: user row
    alt valid credentials
        API-->>U: 200 OK + token
    else invalid
        API-->>U: 401 Unauthorized
    end
    deactivate API
```

Arrow types:

| Syntax | Meaning |
|---|---|
| `->>` | Solid arrowhead (sync request) |
| `-->>` | Dashed arrowhead (response) |
| `->` | Solid line, no arrowhead |
| `-->` | Dotted line, no arrowhead |
| `-x` | Cross at the end |
| `--)` | Open arrowhead (async, 10.3+) |
| `-)` | Solid line, open arrowhead |

Blocks:

- `alt ... else ... end`: alternatives.
- `opt ... end`: optional.
- `loop ... end`: repetition.
- `par ... and ... end`: parallel.
- `critical ... option ... end`: must-succeed section (10.3+).
- `break ... end`: flow-stopping case.
- `rect rgb(r,g,b) ... end`: colored background region.

Participants:

- `participant Name` and `actor Name` (10.3+); alias with `participant A as Alice`.
- `create participant X` / `destroy X` around messages to show lifecycle (11.0+).
- `box colour Label ... end` groups participants visually (10.3+).

Extras:

- `autonumber` numbers messages; `autonumber 5 "[-]"` sets start and format.
- `activate A` / `deactivate A` or shorthand `+` / `-` in the arrow: `A->>+B: msg`.
- `Note over A,B: text`, `Note left of A: text`, `Note right of B: text`.
- Line breaks in messages with `<br/>`.
- `Info` block for a titled header panel.

## ZenUML (`zenuml`)

ZenUML writes sequences as executable-looking pseudo-code. Use when the user prefers code style or the flow is deeply nested.

```
zenuml
    title Login
    User->Api: login(user, pwd) {
        Api->Db: findUser(user)
        Db-->Api: record
        if (record valid) {
            Api-->User: token
        } else {
            Api-->User: 401
        }
    }
```

- Participants are declared implicitly on first use; explicit declaration: `participant Api`.
- `@Actor` annotation marks an actor: `@Actor User->Api: request`.
- Messages return with `-->`; nested braces scope a message's callees.
- Control flow uses plain `if`/`else`, `for`/`while`, `opt`, `par` keywords in code position.
- `try { ... } catch (e) { ... }` is supported.
- Comments with `//`.

## Choosing Between Them

- `sequenceDiagram` renders on GitHub and is the safe default.
- `zenuml` expresses nesting and branching more compactly but is less widely supported in Markdown viewers.
