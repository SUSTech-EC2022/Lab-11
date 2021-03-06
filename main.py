import random
import argparse
import numpy as np
from ai_game import Game
from settings import *
import os

class Individual:
    """Individual in population of Genetic Algorithm.
    Attributes:
        genes: A list which can transform to weight of Neural Network.
        score: Score of the snake played by its Neural Network.
        steps: Steps of the snake played by its Neural Network.
        fitnees: Fitness of Individual.
        seed: The random seed of the game, saved for reproduction.
    """
    def __init__(self, genes):
        self.genes = genes
        self.score = 0
        self.steps = 0
        self.fitness = 0
        self.seed = None
    
    def get_fitness(self):
        """Get the fitness of Individual."""
        game = Game([self.genes])
        self.score, self.steps, self.seed = game.play()
        self.fitness = (self.score + 1 / self.steps) * 100000

class GA:
    """Genetic Algorithm.
    Attributes:
        p_size: Size of the parent generation.
        c_size: Size of the child generation.
        genes_len: Length of the genes.
        mutate_rate: Probability of the mutation.
        population: A list of individuals.
        best_individual: Individual with best fitness.
        avg_score: Average score of the population.
    """
    def __init__(self, p_size=P_SIZE, c_size=C_SIZE, genes_len=GENES_LEN, mutate_rate=MUTATE_RATE):
        self.p_size = p_size
        self.c_size = c_size
        self.genes_len = genes_len
        self.mutate_rate = mutate_rate
        self.population = []
        self.best_individual = None
        self.avg_score = 0

    def generate_ancestor(self):
        for i in range(self.p_size):
            genes = np.random.uniform(-1, 1, self.genes_len)
            self.population.append(Individual(genes))
    
    def inherit_ancestor(self):
        """Load genes from './genes/all/{i}', i: the ith individual."""
        for i in range(self.p_size):
            pth = os.path.join("genes", "all", str(i))
            with open(pth, "r") as f:
                genes = np.array(list(map(float, f.read().split())))
                self.population.append(Individual(genes))

    def crossover(self, c1_genes, c2_genes):
        """Single point crossover."""
        point = np.random.randint(0, self.genes_len)
        c1_genes[:point + 1], c2_genes[:point + 1] = c2_genes[:point + 1], c1_genes[:point + 1]

    def mutate(self, c_genes):  
        """Gaussian mutation with scale of 0.2."""
        mutation_array = np.random.random(c_genes.shape) < self.mutate_rate
        mutation = np.random.normal(size=c_genes.shape)
        mutation[mutation_array] *= 0.2
        c_genes[mutation_array] += mutation[mutation_array]

    def elitism_selection(self, size):
        """Select the top #size individuals to be parents."""
        population = sorted(self.population, key =lambda individual: individual.fitness, reverse=True)
        return population[:size]

    def roulette_wheel_selection(self, size):
        selection = []
        wheel = sum(individual.fitness for individual in self.population)
        for _ in range(size):
            pick = np.random.uniform(0, wheel)
            current = 0
            for individual in self.population:
                current += individual.fitness
                if current > pick:
                    selection.append(individual)
                    break
        
        return selection

    def evolve(self):
        '''The main procss of Genetic Algorithm.'''
        sum_score = 0
        for individual in self.population:
            individual.get_fitness()
            sum_score += individual.score
        self.avg_score = sum_score / len(self.population)

        self.population = self.elitism_selection(self.p_size)  # Select parents to generate children.
        self.best_individual = self.population[0]
        random.shuffle(self.population)

        # Generate children.
        children = []
        while len(children) < self.c_size:
            p1, p2 = self.roulette_wheel_selection(2)
            c1_genes, c2_genes = p1.genes.copy(), p2.genes.copy()
            self.crossover(c1_genes, c2_genes)
            self.mutate(c1_genes)
            self.mutate(c2_genes)
            c1, c2 = Individual(c1_genes), Individual(c2_genes)
            children.extend([c1, c2])

        random.shuffle(children)
        self.population.extend(children)

    def save_best(self):
        """Save the best individual that can get #score score so far."""
        score = self.best_individual.score
        genes_pth= os.path.join("genes", "best", str(score))
        with open(genes_pth, "w") as f:
            for gene in self.best_individual.genes:
                f.write(str(gene) + " ") 
        seed_pth = os.path.join("seed", str(score))
        with open(seed_pth, "w") as f:
            f.write(str(self.best_individual.seed)) 

    def save_all(self):
        """Save the population."""
        for individual in self.population:
            individual.get_fitness()
        population = self.elitism_selection(self.p_size)
        for i in range(len(population)):
            pth = os.path.join("genes", "all", str(i))
            with open(pth, "w") as f:
                for gene in self.population[i].genes:
                    f.write(str(gene) + " ") 

if __name__ == '__main__':

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('-i', '--inherit', action="store_true", 
                         help="Whether to load genes from path ./genes/all.")

    parser.add_argument('-s', '--show', action="store_true", help='whether to show the best individual to play snake after each envolve.')
    args = parser.parse_args()

    ga = GA()
    
    if args.inherit:
        ga.inherit_ancestor()
    else:
        ga.generate_ancestor()

    generation = 0
    record = 0
    while True:
        generation += 1
        ga.evolve()
        print("generation:", generation, ", record:", record,
              ", best score:", ga.best_individual.score, ", average score:", ga.avg_score)
        if ga.best_individual.score >= record:
            record = ga.best_individual.score 
            ga.save_best()
        if args.show:
            genes = ga.best_individual.genes
            seed = ga.best_individual.seed
            game = Game(show=True, genes_list=[genes], seed=seed)
            game.play()
    
        # Save the population every 20 generation.
        if generation % 20 == 0:
            ga.save_all()
