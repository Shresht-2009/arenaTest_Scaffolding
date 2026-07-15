from .generators import GENERATOR_REGISTRY
Generator = GENERATOR_REGISTRY["planning"]
def create_generator():
    return Generator()
