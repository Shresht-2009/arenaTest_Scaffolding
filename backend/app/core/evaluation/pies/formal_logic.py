from .generators import GENERATOR_REGISTRY
Generator = GENERATOR_REGISTRY["formal_logic"]
def create_generator():
    return Generator()
