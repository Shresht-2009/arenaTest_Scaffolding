from .generators import GENERATOR_REGISTRY
Generator = GENERATOR_REGISTRY["scientific_reasoning"]
def create_generator():
    return Generator()
