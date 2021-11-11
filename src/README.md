# Reason for the symlink to `../data/fonts`

Fonts are not source code. Thus they don't belong in `src/`. I put them in
`data/` instead. In order to be accessible when installed, they need
to be part of a package.

Unfortunately, due to an
[annoying bug in setuptools](https://github.com/pypa/setuptools/issues/230),
I had to symlink `dymoprint_fonts` here so that `pip install --editable .`
works. Namely, the resulting egg-link can only see `src/`. In contrast,
`pip install .` makes an actual `dymoprint_fonts` package directory.
