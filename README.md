# DAYamlChecker

An LSP for Docassemble YAML Interviews

## How to run

```bash
pip install .
dayaml check              # defaults to ./docassemble
dayaml format             # defaults to ./docassemble
dayaml check path/to/yaml-or-dir
dayaml check --show-experimental path/to/yaml-or-dir
dayaml format path/to/interview.yml

# Backwards-compatible entry points
python3 -m dayamlchecker `find . -name "*.yml" -path "*/questions/*" -not -path "*/.venv/*" -not -path "*/build/*"` # i.e. a space separated list of files
dayamlchecker `find . -name "*.yml" -path "*/questions/*" -not -path "*/.venv/*" -not -path "*/build/*"`
dayamlchecker-fmt path/to/interview.yml
```

## Message Codes

Validation output now includes stable message codes in the style of tools like pylint:

```text
[E301] At interview.yml:12: Keys that shouldn't exist! ['not_a_real_key']
```

Use `dayaml check --show-experimental ...` to include the legacy `REAL ERROR:`
prefix for non-experimental errors.

### Real Errors

| Code | Meaning |
| --- | --- |
| `E101` | Duplicate YAML key |
| `E102` | YAML parsing error |
| `E201` | Jinja2 syntax error |
| `E202` | Jinja2 template error |
| `E301` | Unknown YAML keys |

### Warnings

| Code | Meaning |
| --- | --- |
| `W101` | Value should be a YAML string |
| `W111` | Invalid Mako syntax |
| `W112` | Mako compile error |
| `W121` | Python code block must be a YAML string |
| `W122` | Python syntax error |
| `W201` | JavaScript modifier must be a string |
| `W202` | Invalid JavaScript syntax |
| `W203` | JavaScript modifier must contain at least one `val()` call |
| `W204` | `val()` references a field not defined on this screen |
| `W205` | `val()` argument must be a quoted string literal |
| `W301` | Malformed `show if` shorthand |
| `W302` | `show if: code` must be a YAML string |
| `W303` | `show if: code` has a Python syntax error |
| `W304` | `show if` dict must include `variable` or `code` |
| `W401` | Python variable reference must be a YAML string |
| `W402` | Python variable reference cannot contain whitespace |
| `W403` | `objects` block must be a list or dict |
| `W404` | `fields: code` must be a YAML string |
| `W405` | Bare `fields` dict has no recognized field or `code` key |
| `W406` | `fields` must be a list or dict |
| `W407` | Field modifier `variable` must be a string |
| `W408` | Field modifier `variable` references a field not defined on this screen |
| `W409` | Field modifier `code` contains another validation error |
| `W410` | `show if: code` references a variable defined on the same screen |
| `W411` | Field modifier dict must include `variable` or `code` |
| `W412` | Field modifier shorthand references a field not defined on this screen |
| `W601` | No recognized block type found |
| `W602` | Block matches too many exclusive interview types |
| `W603` | Interview-order block is missing a matching show/hide guard |
| `W604` | Show/hide visibility logic is nested too deeply |

### Conventions

| Code | Meaning |
| --- | --- |
| `C101` | `validation code` should call `validation_error()` |
