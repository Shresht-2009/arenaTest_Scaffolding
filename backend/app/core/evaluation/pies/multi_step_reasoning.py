from .generators import GENERATOR_REGISTRY
Generator = GENERATOR_REGISTRY["multi_step_reasoning"]
def create_generator():
    return Generator()
