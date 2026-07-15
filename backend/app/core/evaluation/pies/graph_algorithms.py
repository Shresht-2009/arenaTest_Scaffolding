from .generators import GENERATOR_REGISTRY
Generator = GENERATOR_REGISTRY["graph_algorithms"]
def create_generator():
    return Generator()
