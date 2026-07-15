from .generators import GENERATOR_REGISTRY
Generator = GENERATOR_REGISTRY["strategic_games"]
def create_generator():
    return Generator()
