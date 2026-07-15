from .generators import GENERATOR_REGISTRY
Generator = GENERATOR_REGISTRY["debugging"]
def create_generator():
    return Generator()
