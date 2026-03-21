import random

def mutate_strategy_params(params: dict) -> dict:
    mutated = params.copy()
    for k in mutated:
        if isinstance(mutated[k], (int, float)):
            mutated[k] *= random.uniform(0.9, 1.1)
    return mutated

def crossover(parent1: dict, parent2: dict) -> dict:
    return {k: random.choice([parent1[k], parent2[k]]) for k in parent1}

def fitness_function(sim_result: dict) -> float:
    return sim_result["roi_percent"] * sim_result["winrate"]

def evolve_population(population: list, simulate_fn, price_series: list, generations: int = 10) -> dict:
    for _ in range(generations):
        evaluated = []
        for strat in population:
            result = simulate_fn(price_series, strat["name"], **strat["params"])
            score = fitness_function(result)
            evaluated.append((score, strat))

        evaluated.sort(reverse=True, key=lambda x: x[0])
        parents = [s for _, s in evaluated[:2]]

        # Mutación y cruce
        population = []
        for _ in range(10):
            child = crossover(parents[0]["params"], parents[1]["params"])
            population.append({
                "name": parents[0]["name"],
                "params": mutate_strategy_params(child)
            })

    return parents[0]