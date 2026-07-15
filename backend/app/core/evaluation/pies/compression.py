from .generators import GENERATOR_REGISTRY
Generator = GENERATOR_REGISTRY["compression"]
def create_generator():
    return Generator()
