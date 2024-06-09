
from cat.utils import singleton
from cat.memory.vector_memory import VectorMemory
from cat.memory.knowledge_graph import KnowledgeGraph

# This class represents the Cat long term memory (content the cat saves on disk).
# @singleton
class LongTermMemory:
    """Cat's non-volatile memory.

    This is an abstract class to interface with the Cat's vector memory collections.

    Attributes
    ----------
    vectors : VectorMemory
        Vector Memory collection.
    """
    def __init__(self):
        # Vector based memory (will store embeddings and their metadata)
        self.vectors = VectorMemory()

        # Knowledge Graph
        self.kg = KnowledgeGraph()

