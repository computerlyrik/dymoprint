# Vendored dependencies

This directory contains vendored dependencies managed by the
[`vendoring`](https://github.com/pradyunsg/vendoring) tool.

## Updating dependencies

To update the vendored dependencies, run:

```bash
vendoring update
```

## Packages vendored

### [`matplotlib`](https://github.com/matplotlib/matplotlib/)

We take just a subset of `font_manager.py` used for selecting fonts. See [LICENSE](../src/dymoprint/_vendor/matplotlib/LICENSE) for the license.

## Coding style

Test code using the following command:

```bash
pylint src --disable invalid-name,missing-module-docstring,missing-function-docstring,too-many-arguments,too-many-locals,import-error,line-too-long,too-many-instance-attributes,missing-class-docstring,too-many-statements,too-few-public-methods
```
