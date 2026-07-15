from .generators import GENERATOR_REGISTRY
Generator = GENERATOR_REGISTRY["counterfactual_reasoning"]
def create_generator():
    return Generator()
