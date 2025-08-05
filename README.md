## Running
1. Install [uv](https://docs.astral.sh/uv/#installation) (see link)
1. In a terminal, `cd` into `src/matrix_data_collection` folder
2. Run `uv sync` which will install Python and all needed dependencies
3. Run `flask run --debug`
    * It looks for the `app.py` file in the current folder
    * `--debug` tells flask to reload any files that change (python, html, etc.), so you don't have to re-run the command every time you make tweaks
4. Open a web browser at the address flask specifies

## Recommended Tools
*Note:* this is the dev setup I use. Feel free to use others as preferred.

* VS Code with Extensions (optional, but helpful):
    * Python
    * Dragon Jinja - for jinja html template files
    * Jinja Snippets
    * Ruff - python linting
* [uv](https://docs.astral.sh/uv/) - simple and fast way to install Python and dependencies
* [SQLite Studio Portable](https://github.com/pawelsalawa/sqlitestudio/releases) - helpful for viewing/editing sqlite databases

## Helpful Docs
* [Flask](https://flask.palletsprojects.com/en/stable/quickstart/) - Simple Python web app framework
* [Jinja](https://jinja.palletsprojects.com/en/stable/templates/#) - HTML (and other) templates with Flask integration
* [SQLite](https://www.sqlite.org/lang_select.html) - Simple database with good Python integration
* [Python sqlite3 docs](https://docs.python.org/3/library/sqlite3.html) - Built-in SQLite interface
* [Pico.css](https://picocss.com/docs/forms) - Minimal CSS framework for styling pages
