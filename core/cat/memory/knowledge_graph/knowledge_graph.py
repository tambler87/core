
import os
import shutil
import json

# https://kuzudb.com/api-docs/python/kuzu.html
import kuzu

from cat.env import get_env
from cat.log import log
from cat.utils import hash_password


class KnowledgeGraph:
    """Yes, we are doing it."""
    
    def __init__(self, dir_path=None):

        if dir_path is None:
            dir_path = "cat/data/local_knowledge_graph"

        #if True: # TODOGRAPH: create it if the file does not exist
        shutil.rmtree(dir_path)

        os.makedirs(dir_path, exist_ok=True)
        self.kg = kuzu.Database(dir_path)

        # Populate initial graph
        self.create_base_graph()

    # NOTE: not all DBs supporting Cypher require a description of nodes and relations before insertion)
    def create_base_graph(self):


        # User type
        self("CREATE NODE TABLE User(name STRING, password_hash STRING, role STRING, PRIMARY KEY (name))")
        # Admin user
        admin_user_dict = {
            "name": "admin",
            "password_hash": hash_password("admin"),
            "role": "admin"
        }
        self.create_node("User", admin_user_dict)

        # Permission
        self("CREATE NODE TABLE Permission(name STRING, PRIMARY KEY (name))")
        self("CREATE REL TABLE Can(FROM User TO Permission)")
        # TODO: define minimal permissions and roles

        # Setting
        # NOTE: since setting value is a free dict, it is encoded as a string
        self("CREATE NODE TABLE Setting(name STRING, value STRING, category STRING, PRIMARY KEY (name))")
        # Migrate settings from legacy metadata.json
        legacy_sqlite_db_content = self.migrate_legacy_sqlite()
       






        res = self("""
            MATCH (s:Setting)
            RETURN s
        """)
        #log.warning(res)
        #res = self("""
        #    MATCH (u:User)-[c:Can]->(p:Permission)
        #    RETURN u.name, p.name;        
        #""")

        while res.has_next():
            log.warning(res.get_next())


    def create_node(self, node_type, attributes):
        query = f"CREATE (node:{node_type} {{"
        for k, v in attributes.items():
            # `$k` will be substituted by actual value
            query += f"{k}: ${k}, "
        query = query[:-2] + "}) RETURN node"
        
        return self(query, params=attributes)
        

    def migrate_legacy_sqlite(self):

        db_file = get_env("CCAT_METADATA_FILE")
        if not os.path.exists(db_file):
            return
        
        with open(db_file) as f:
            db = json.load(f)

        db = db["_default"]
        for _, record in db.items():
            log.info(record)
            record_dict = {
                "name": record["name"],
                # I know this is ugly, Setting values are freeform
                "value": json.dumps(record["value"]),
                "category": record["category"]
            }
            self.create_node("Setting", record_dict)



    def __call__(self, query: str, params=None):

        try:
            with kuzu.Connection(self.kg) as connection:
                result = connection.execute(query, params)
            return result
        except Exception as e:
            log.error(e)
        
