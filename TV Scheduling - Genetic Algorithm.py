import random
import csv
import streamlit as st

GEN = 100
POP = 50
EL_S = 2

st.title("TV Scheduling Using Genetic Algorithm")

CO_R = st.slider(
    "Crossover Rate",
    min_value=0.0,
    max_value=0.95,
    value=0.8,
    step=0.05
)

MUT_R = st.slider(
    "Mutation Rate",
    min_value=0.01,
    max_value=0.50,
    value=0.2,
    step=0.01
)
run_button = st.button("Generate Schedule")

# Function to read the CSV file and convert it to the desired format
def read_csv_to_dict(file_path):
    program_ratings = {}
    
    with open(file_path, mode='r', newline='') as file:
        reader = csv.reader(file)
        # Skip the header
        header = next(reader)
        
        for row in reader:
            if not row :
                continue
            program = row[0]
            ratings = [float(x) for x in row[1:]]  # Convert the ratings to floats
            program_ratings[program] = ratings
    
    return program_ratings

# Path to the CSV file
file_path = r"C:\Users\User\Downloads\GA tv scheduling\program_ratings.csv"

# Get the data in the required format
program_ratings_dict = read_csv_to_dict(file_path)

# Print the result (you can also return or process it further)
for program, ratings in program_ratings_dict.items():
    print(f"'{program}': {ratings},")




##################################### DEFINING PARAMETERS AND DATASET ################################################################
# Sample rating programs dataset for each time slot.
ratings = program_ratings_dict

all_programs = list(ratings.keys()) # all programs
all_time_slots = list(range(6, 24)) # time slots

######################################### DEFINING FUNCTIONS ########################################################################
# defining fitness function
def fitness_function(schedule):
    total_rating = 0
    for time_slot, program in enumerate(schedule):
        total_rating += ratings[program][time_slot]
    return total_rating

# initializing the population
def initialize_pop(programs, time_slots):
    if not programs:
        return [[]]

    all_schedules = []
    for i in range(len(programs)):
        for schedule in initialize_pop(programs[:i] + programs[i + 1:], time_slots):
            all_schedules.append([programs[i]] + schedule)

    return all_schedules

# selection
def finding_best_schedule(all_schedules):
    best_schedule = []
    max_ratings = 0

    for schedule in all_schedules:
        total_ratings = fitness_function(schedule)
        if total_ratings > max_ratings:
            max_ratings = total_ratings
            best_schedule = schedule

    return best_schedule

# calling the pop func.
#all_possible_schedules = initialize_pop(all_programs, all_time_slots)

# callin the schedule func.
#best_schedule = finding_best_schedule(all_possible_schedules)


############################################# GENETIC ALGORITHM #############################################################################

# Crossover
def crossover(schedule1, schedule2):
    crossover_point = random.randint(1, len(schedule1) - 2)
    child1 = schedule1[:crossover_point] + schedule2[crossover_point:]
    child2 = schedule2[:crossover_point] + schedule1[crossover_point:]
    return child1, child2

# mutating
def mutate(schedule):
    mutation_point = random.randint(0, len(schedule) - 1)
    new_program = random.choice(all_programs)
    schedule[mutation_point] = new_program
    return schedule

# calling the fitness func.
def evaluate_fitness(schedule):
    return fitness_function(schedule)

# genetic algorithms with parameters

def genetic_algorithm(
    initial_schedule,
    generations=GEN,
    population_size=POP,
    crossover_rate=CO_R,
    mutation_rate=MUT_R,
    elitism_size=EL_S
):

    population = [initial_schedule]
    history = []

    best_overall_schedule = None
    best_overall_rating = -1

    for _ in range(population_size - 1):
        random_schedule = initial_schedule.copy()
        random.shuffle(random_schedule)
        population.append(random_schedule)

    for generation in range(generations):

        new_population = []

        population.sort(
            key=lambda schedule: fitness_function(schedule),
            reverse=True
        )

        new_population.extend(population[:elitism_size])

        while len(new_population) < population_size:

            parent1, parent2 = random.choices(population, k=2)

            if random.random() < crossover_rate:
                child1, child2 = crossover(parent1, parent2)
            else:
                child1, child2 = parent1.copy(), parent2.copy()

            if random.random() < mutation_rate:
                child1 = mutate(child1)

            if random.random() < mutation_rate:
                child2 = mutate(child2)

            new_population.extend([child1, child2])

        population = new_population[:population_size]

        # Find best schedule for this generation
        population.sort(
            key=lambda schedule: fitness_function(schedule),
            reverse=True
        )

        best_ga_schedule = population[0]

        # Build the full 18-hour schedule
        remaining_slots = len(all_time_slots) - len(initial_schedule)

        generation_schedule = (
            initial_schedule +
            best_ga_schedule[:remaining_slots]
        )

        generation_rating = fitness_function(generation_schedule)

        if generation_rating > best_overall_rating:
            best_overall_rating = generation_rating
            best_overall_schedule = generation_schedule.copy()

        history.append({
            "Generation": generation + 1,
            "Best Rating": round(generation_rating, 2),
            "Best Schedule": " → ".join(generation_schedule)
        })

    return best_overall_schedule, history
##################################################### RESULTS ###################################################################################

if run_button:

    all_possible_schedules = []

    for _ in range(POP):
        schedule = all_programs.copy()
        random.shuffle(schedule)
        all_possible_schedules.append(schedule)

    initial_best_schedule = finding_best_schedule(all_possible_schedules)

    rem_t_slots = len(all_time_slots) - len(initial_best_schedule)

    genetic_schedule, history = genetic_algorithm(
        initial_best_schedule,
        generations=GEN,
        population_size=POP,
        crossover_rate=CO_R,
        mutation_rate=MUT_R,
        elitism_size=EL_S
    )

    final_schedule = genetic_schedule

    st.write("Crossover Rate:", CO_R)
    st.write("Mutation Rate:", MUT_R)
    st.subheader("Final Optimal Schedule")

    schedule_table = []

    for time_slot, program in enumerate(final_schedule):
        schedule_table.append({
            "Time Slot": f"{all_time_slots[time_slot]:02d}:00",
            "Program": program
        })

    st.table(schedule_table)
    st.write("Total Ratings:", round(fitness_function(final_schedule), 2))
    st.success("Schedule generated successfully!")
    st.subheader("Evolution of Best Schedule")
    st.dataframe(history, use_container_width=True)