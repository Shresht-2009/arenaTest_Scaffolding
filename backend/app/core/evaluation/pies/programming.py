from .generators import GENERATOR_REGISTRY
Generator = GENERATOR_REGISTRY["programming"]
def create_generator():
    return Generator()
