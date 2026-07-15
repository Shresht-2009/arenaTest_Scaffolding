from .generators import GENERATOR_REGISTRY
Generator = GENERATOR_REGISTRY["abstract_reasoning"]
def create_generator():
    return Generator()
