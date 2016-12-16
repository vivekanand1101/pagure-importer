import click
from pagure_importer.app import app
from pagure_importer.utils import create_config

@app.command()
def mkconfig():
    create_config()