from .generators import GENERATOR_REGISTRY
Generator = GENERATOR_REGISTRY["scheduling"]
def create_generator():
    return Generator()
