from .generators import GENERATOR_REGISTRY
Generator = GENERATOR_REGISTRY["information_reconstruction"]
def create_generator():
    return Generator()
