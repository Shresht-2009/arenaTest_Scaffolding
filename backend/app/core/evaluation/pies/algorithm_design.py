from .generators import GENERATOR_REGISTRY
Generator = GENERATOR_REGISTRY["algorithm_design"]
def create_generator():
    return Generator()
