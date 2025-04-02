# kvm

*Kubectl Version Manager*: Seamlessly switch between multiple `kubectl` versions.

![KVM by Dalle-2](./img/kvm.png)

KVM by Dalle-2

## TL;DR

### Install

```python
pip install .
python3 -m kvm version
```

### Use

```python
python3 -m kvm download
```

![KVM usage example](./img/kvm-example.png)

## TODOs

1. Add installation to $PATH.
2. Build with Pyinstaller as executable.
3. Distribute over Pip.
4. Extend Unit Testing coverage

## Development

### Prepare your environment

Create a Virtual Environment:

```bash
python -m venv venv
source venv/bin/activate
```

Install the dependencies:

```bash
pip install -r development.txt -r requirements.txt
```

### Unit Testing

Run Pytest and calculate coverage:

```bash
pytest tests --cov=kvm
```
