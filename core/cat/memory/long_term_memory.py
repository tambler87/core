from cat.memory.vector_memory import VectorMemory
from cat.memory.knowledge_graph import KnowledgeGraph

# This class represents the Cat long term memory (content the cat saves on disk).
class LongTermMemory:
    """Cat's non-volatile memory.

    This is an abstract class to interface with the Cat's vector memory collections.

    Attributes
    ----------
    vectors : VectorMemory
        Vector Memory collection.
    """
    def __init__(self, vector_memory_config={}):
        # Vector based memory (will store embeddings and their metadata)
        self.vectors = VectorMemory(**vector_memory_config)

        # Knowledge Graph
        self.kg = KnowledgeGraph()

