# No more "ROC login"s!

## Intro

This tool automates logging in with your creds to skip the messy OneCloud login and multiple browser tabs kept open in background.

Right now it reads your credentials from .env file. So, make sure to create a new .env file in your cloned project root:

```bash
# .env
username=<USERNAME>
password=<PASSWORD>

```

## Installation

Managed by Poetry, so make sure it's [installed in your system](https://python-poetry.org/docs/#installing-with-the-official-installer).
Then, simply do `poetry install` and voila! You have a new virtual environment, containing necessary selenium deps and libraries.

Try it out with:

```bash
poetry run fck-roc-login --help
```

## Shell support

### Fish function

Create a new function file in `~/.config/fish/functions/roc.fish`:

```fish
function fck-roc-login --argument-names cluster --description "Wrapper around python module of fck-roc-login"
  set ROC_DIR "$HOME/projects/fck-roc-login/" # put cloned repo path
  env ROC_ENV_FILE="$ROC_DIR/.env" poetry run -C "$ROC_DIR" -- fck-roc-login "$cluster"
end

```

## Future Roadmap

1. Add support of existing User's profile so selenium can reuse the credentials from saved password manager.
