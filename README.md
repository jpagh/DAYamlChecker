# DAYamlChecker

An LSP for Docassemble YAML Interviews

## How to run

```bash
pip install .
dayaml check              # defaults to ./docassemble
dayaml format             # defaults to ./docassemble
dayaml check path/to/yaml-or-dir
dayaml format path/to/interview.yml

# Backwards-compatible entry points
python3 -m dayamlchecker `find . -name "*.yml" -path "*/questions/*" -not -path "*/.venv/*" -not -path "*/build/*"` # i.e. a space separated list of files
dayamlchecker `find . -name "*.yml" -path "*/questions/*" -not -path "*/.venv/*" -not -path "*/build/*"`
dayamlchecker-fmt path/to/interview.yml
```
