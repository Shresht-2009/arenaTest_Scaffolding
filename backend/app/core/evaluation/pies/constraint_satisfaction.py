from .generators import GENERATOR_REGISTRY
Generator = GENERATOR_REGISTRY["constraint_satisfaction"]
def create_generator():
    return Generator()
