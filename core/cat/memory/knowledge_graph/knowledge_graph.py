
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
    
    def __init__(self, kg_path=None):

        if kg_path is None:
            kg_path = self.get_folder_name()
        self.db_path = kg_path

        shutil.rmtree(kg_path, ignore_errors=True) 
        
        to_populate = not os.path.exists(kg_path)
        if to_populate:
            os.makedirs(kg_path)

        # don't know if this can be kept as instance attribute
        # https://kuzudb.com/api-docs/python/kuzu.html#Database.close
        self.db = kuzu.Database(self.db_path, lazy_init=True)
        #self.db_connection = kuzu.Connection(self.db)

        # Populate initial graph
        if to_populate:
            self.create_base_graph()

    def get_folder_name(self):
        return "cat/data/local_knowledge_graph"

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

        #while res.has_next():
        #    log.warning(res.get_next())


    def create_node(self, node_type, attributes):
        query = f"CREATE (node:{node_type} {{"
        for k, v in attributes.items():
            # `$k` will be substituted by actual value
            query += f"{k}: ${k}, "
        query = query[:-2] + "}) RETURN node"
        
        return self(query, params=attributes)
        

    def migrate_legacy_sqlite(self):
        from cat.db.database import Database
        db_file = Database().get_file_name() #get_env("CCAT_METADATA_FILE")
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
        # on multithreading:
        # https://github.com/kuzudb/kuzu/issues/3260#issuecomment-2051898996
        try:
            with kuzu.Connection(self.db) as connection:
                result = connection.execute(query, params)
            return result
            #result = self.db_connection.execute(query, params) 
        except Exception as e:
            log.error(e)

        
        
