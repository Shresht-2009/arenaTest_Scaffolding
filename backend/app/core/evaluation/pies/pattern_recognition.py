from .generators import GENERATOR_REGISTRY
Generator = GENERATOR_REGISTRY["pattern_recognition"]
def create_generator():
    return Generator()
