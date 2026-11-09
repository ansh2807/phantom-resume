# Contributing

Use Python 3.10 or newer in a virtual environment. Install `requirements.txt`, then run:

```bash
python -m unittest discover -s tests -v
```

For a manual document check, generate fixtures with `python examples/create_demo.py`. Keep originals and outputs separate. Tests that mutate documents must use temporary directories or ignored demo output paths.

Before opening a pull request:

1. Describe the observed problem and the changed behavior.
2. Include focused verification. Do not use live applications as tests.
3. Review staged files for personal information, credentials, resumes, screenshots, logs, and databases.
4. Document whether a new channel is locally verified, experimentally supported, or untested.

Browser tests must be mocked or target an explicitly authorized test environment. Never make network access or application submission part of CI. Preserve the read-only contract of `--probe-only`.

To regenerate the README artwork, run `python scripts/render_readme_assets.py`. The renderer uses generated shapes and synthetic labels; it never loads a candidate document or browser screenshot.
