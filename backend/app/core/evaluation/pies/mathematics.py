from .generators import GENERATOR_REGISTRY
Generator = GENERATOR_REGISTRY["mathematics"]
def create_generator():
    return Generator()
