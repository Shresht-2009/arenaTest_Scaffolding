from .generators import GENERATOR_REGISTRY
Generator = GENERATOR_REGISTRY["optimization"]
def create_generator():
    return Generator()
