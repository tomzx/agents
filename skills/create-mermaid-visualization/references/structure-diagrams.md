# Structure Diagrams Reference

Class, state, and entity relationship diagrams describe structure rather than flow.

## Class Diagrams (`classDiagram`)

```
classDiagram
    direction LR
    class Shape {
        <<interface>>
        +int area
        +draw() void
    }
    class Circle {
        +float radius
    }
    Shape <|.. Circle
```

- Members: `+` public, `-` private, `#` protected, `~` generic.
- Return types after parentheses: `+get(int id) Order`.
- Stereotypes in guillemets: `<<interface>>`, `<<abstract>>`, `<<enumeration>>` with members as the values.
- Generic types: `class List~T~`.

Relationship operators:

| Operator | Meaning |
|---|---|
| `<|--` | Inheritance (extends) |
| `*--` | Composition (solid diamond) |
| `o--` | Aggregation (hollow diamond) |
| `-->` | Association (arrow) |
| `--` | Solid link |
| `<|..` | Realization (implements) |
| `..>` | Dependency |

Add labels and multiplicity: `Customer "1" --> "many" Order : places`.
Annotations on relationships: `A .. B : <<uses>>`.

## State Diagrams (`stateDiagram-v2`)

Always use `stateDiagram-v2`; the unversioned keyword renders with the old renderer.

```
stateDiagram-v2
    [*] --> Idle
    Idle --> Running : start
    Running --> Paused : pause
    Paused --> Running : resume
    Running --> [*] : stop

    state Running {
        [*] --> Step1
        Step1 --> Step2
    }
```

- `[*]` is the initial or final pseudo-state.
- Composite states nest with indentation inside a `state Name { ... }` block.
- Concurrent (fork/join) regions with `state X { state "a" as a }` plus `--` separators inside composite states.
- Choice: `state ok <<choice>>` then `Running --> ok`, `ok --> A : yes`, `ok --> B : no`.
- Notes: `note right of Idle : text` or a block form.
- Aliases: `state "Long name" as short`.
- Transitions can carry star ratings in journey contexts, but keep labels plain text.

## Entity Relationship Diagrams (`erDiagram`)

```
erDiagram
    CUSTOMER ||--o{ ORDER : places
    ORDER ||--|{ LINE_ITEM : contains
    PRODUCT }o--o{ ORDER : "ordered in"

    CUSTOMER {
        int id PK
        string email UK
        string name
        datetime created_at
    }
```

Crow's foot cardinality, read both sides:

| Left | Right | Meaning |
|---|---|---|
| `||` | `||` | Exactly one to exactly one |
| `||` | `o{` | One to zero or many |
| `||` | `\|{` | One to one or many |
| `}o` | `o{` | Zero or many to zero or many |
| `\|o` | `\|{` | Zero or one to one or many |

Attribute keys: `PK` primary, `FK` foreign, `UK` unique. Add comments after attributes with double quotes: `string status "pending or shipped"`.

Relationships can carry labels and attribute-less entities are valid: `A ||--o{ B : has`.
Style entity blocks with `style CUSTOMER fill:#F4F4F4`.
