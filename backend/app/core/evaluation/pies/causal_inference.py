from .generators import GENERATOR_REGISTRY
Generator = GENERATOR_REGISTRY["causal_inference"]
def create_generator():
    return Generator()
