from .generators import GENERATOR_REGISTRY
Generator = GENERATOR_REGISTRY["knowledge_integration"]
def create_generator():
    return Generator()
