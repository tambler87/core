import os
import shutil

from typing import Any
from typing import Generator

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient


from cat.db.database import Database
from cat.log import log

import cat.utils as utils

from qdrant_client import QdrantClient
from cat.memory.vector_memory import VectorMemory
from cat.memory.knowledge_graph import KnowledgeGraph
from cat.mad_hatter.mad_hatter import MadHatter
from cat.mad_hatter.plugin import Plugin

from cat.main import cheshire_cat_api


# substitute classes' methods where necessary for testing purposes
def mock_classes(monkeypatch):

    # Use in memory vector db
    def mock_connect_to_vector_memory(self, *args, **kwargs):
        self.vector_db = QdrantClient(":memory:")
    monkeypatch.setattr(VectorMemory, "connect_to_vector_memory", mock_connect_to_vector_memory)

    # Use a different json settings db
    # TODOGRAPH: delete after KG takes over
    def mock_get_file_name(self, *args, **kwargs):
        return "tests/mocks/metadata-test.json"
    monkeypatch.setattr(Database().__class__, "get_file_name", mock_get_file_name)

    # Use a different knowledge graph db
    def mock_get_folder_name(self, *args, **kwargs):
        return "tests/mocks/local_knowledge_graph_test"
    monkeypatch.setattr(KnowledgeGraph, "get_folder_name", mock_get_folder_name)
 
    # Use mock utils plugin folder
    def get_test_plugin_folder():
        return "tests/mocks/mock_plugin_folder/"
    utils.get_plugins_path = get_test_plugin_folder

    # do not check plugin dependencies at every restart
    def mock_install_requirements(self, *args, **kwargs):
        pass
    monkeypatch.setattr(Plugin, "_install_requirements", mock_install_requirements)


# get rid of tmp files and folders used for testing 
def clean_up_mocks():
    # clean up service files and mocks
    to_be_removed = [
        "cat/metadata-test.json", # legacy position, now moved into mocks folder
        "tests/mocks/metadata-test.json",
        "tests/mocks/local_knowledge_graph_test",
        "tests/mocks/mock_plugin.zip",
        "tests/mocks/mock_plugin/settings.json",
        "tests/mocks/mock_plugin_folder/mock_plugin",
        "tests/mocks/empty_folder"
    ]
    for tbr in to_be_removed:
        if os.path.exists(tbr):
            if os.path.isdir(tbr):
                shutil.rmtree(tbr)
            else:
                os.remove(tbr)


# Main fixture for the FastAPI app
@pytest.fixture(scope="function")
def client(monkeypatch) -> Generator[TestClient, Any, None]:
    """
    Create a new FastAPI TestClient.
    """

    # clean up tmp files and folders
    clean_up_mocks()
    # monkeypatch classes
    mock_classes(monkeypatch)
    # delete all singletons!!!
    utils.singleton.instances = {}
    
    with TestClient(cheshire_cat_api) as client:
        yield client

    # clean up tmp files and folders (useful when tests fail)
    clean_up_mocks()
