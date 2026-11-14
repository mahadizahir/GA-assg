import csv
import random
from pathlib import Path

import streamlit as st


# ---------------------------- DATA AND PARAMETERS ----------------------------
GEN = 100
POP = 50
EL_S = 2


def read_csv_to_dict(file_path):
    program_ratings = {}

    with open(file_path, mode="r", newline="", encoding="utf-8-sig") as file:
        reader = csv.reader(file)
        header = next(reader, None)  # Read the CSV header safely

        if header is None:
            raise ValueError("The CSV file is empty. Please check program_ratings.csv.")

        for row_number, row in enumerate(reader, start=2):
            # Ignore completely blank rows in the CSV file.
            if not row or not any(value.strip() for value in row):
                continue

            program = row[0].strip()
            if not program:
                raise ValueError(
                    f"Missing program name in CSV row {row_number}. "
                    "Please check program_ratings.csv."
                )

            values = []
            for column_number, value in enumerate(row[1:], start=2):
                if not value.strip():
                    raise ValueError(
                        f"Missing rating in CSV row {row_number}, column {column_number}. "
                        "Please fill in the rating or correct the CSV file."
                    )
                try:
                    values.append(float(value))
                except ValueError as error:
                    raise ValueError(
                        f"Invalid rating '{value}' in CSV row {row_number}, "
                        f"column {column_number}. Ratings must be numbers."
                    ) from error

            program_ratings[program] = values

    if not program_ratings:
        raise ValueError("No program data was found in the CSV file.")

    # Every program must have the same number of hourly ratings.
    expected_slots = len(next(iter(program_ratings.values())))
    for program, values in program_ratings.items():
        if len(values) != expected_slots:
            raise ValueError(
                f"Program '{program}' has {len(values)} ratings, but "
                f"{expected_slots} ratings are expected. Please check the CSV file."
            )

    return program_ratings


# ---------------------------- GENETIC ALGORITHM ----------------------------
def fitness_function(schedule, ratings):
    total_rating = 0.0
    for time_slot, program in enumerate(schedule):
        total_rating += ratings[program][time_slot]
    return total_rating


def initialize_population(programs, number_of_slots, population_size):
    population = []

    for _ in range(population_size):
        schedule = []
        for _ in range(number_of_slots):
            schedule.append(random.choice(programs))
        population.append(schedule)

    return population


def select_parent(population, ratings):
    # Tournament selection: pick the strongest of three candidates.
    candidates = random.sample(population, 3)
    best_candidate = candidates[0]

    for candidate in candidates:
        if fitness_function(candidate, ratings) > fitness_function(best_candidate, ratings):
            best_candidate = candidate

    return best_candidate


def crossover(schedule1, schedule2):
    crossover_point = random.randint(1, len(schedule1) - 1)
    child1 = schedule1[:crossover_point] + schedule2[crossover_point:]
    child2 = schedule2[:crossover_point] + schedule1[crossover_point:]
    return child1, child2


def mutate(schedule, programs):
    new_schedule = schedule.copy()
    mutation_point = random.randint(0, len(new_schedule) - 1)
    new_schedule[mutation_point] = random.choice(programs)
    return new_schedule


def genetic_algorithm(ratings, crossover_rate, mutation_rate):
    programs = list(ratings.keys())
    number_of_slots = len(ratings[programs[0]])
    population = initialize_population(programs, number_of_slots, POP)

    for _ in range(GEN):
        population.sort(
            key=lambda schedule: fitness_function(schedule, ratings),
            reverse=True,
        )

        new_population = []
        for index in range(EL_S):
            new_population.append(population[index].copy())

        while len(new_population) < POP:
            parent1 = select_parent(population, ratings)
            parent2 = select_parent(population, ratings)

            if random.random() < crossover_rate:
                child1, child2 = crossover(parent1, parent2)
            else:
                child1 = parent1.copy()
                child2 = parent2.copy()

            if random.random() < mutation_rate:
                child1 = mutate(child1, programs)
            if random.random() < mutation_rate:
                child2 = mutate(child2, programs)

            new_population.append(child1)
            if len(new_population) < POP:
                new_population.append(child2)

        population = new_population

    population.sort(
        key=lambda schedule: fitness_function(schedule, ratings),
        reverse=True,
    )
    return population[0]


# ---------------------------- STREAMLIT CONTROLS ----------------------------
def toggle_mutation_mode():
    # Switch between the default value and the custom slider.
    st.session_state.use_custom_mutation = not st.session_state.use_custom_mutation


st.set_page_config(page_title="TV Scheduling - Genetic Algorithm", layout="wide")
st.title("TV Scheduling Using Genetic Algorithm")
st.write("Set your crossover and mutation rates, then generate a TV schedule.")

if "mutation_slider" not in st.session_state:
    st.session_state.mutation_slider = 0.02
if "use_custom_mutation" not in st.session_state:
    # Start with the assignment's default mutation rate selected.
    st.session_state.use_custom_mutation = False
if "last_result" not in st.session_state:
    st.session_state.last_result = None
if "trial_history" not in st.session_state:
    st.session_state.trial_history = []

file_path = Path(__file__).resolve().parent / "program_ratings.csv"

if not file_path.exists():
    st.error("program_ratings.csv is missing. Put it in the same folder as this Python file.")
    st.stop()

try:
    ratings = read_csv_to_dict(file_path)
except (ValueError, csv.Error) as error:
    st.error(f"Unable to read program_ratings.csv: {error}")
    st.stop()

all_programs = list(ratings.keys())
all_time_slots = []
for hour in range(6, 6 + len(ratings[all_programs[0]])):
    all_time_slots.append(hour)

crossover_rate = st.slider(
    "Crossover Rate (CO_R)",
    min_value=0.0,
    max_value=0.95,
    value=0.80,
    step=0.05,
)

with st.container(border=True):
    st.subheader("Mutation Rate (MUT_R)")

    if st.session_state.use_custom_mutation:
        st.caption("Custom mode: choose a mutation rate between 0.01 and 0.05.")
        custom_mutation_rate = st.slider(
            "Custom mutation rate",
            min_value=0.01,
            max_value=0.05,
            step=0.01,
            key="mutation_slider",
            help="Choose a custom mutation rate between 0.01 and 0.05.",
        )
        mutation_rate = custom_mutation_rate
        st.info(f"Active mutation rate: {mutation_rate:.2f} — Custom")
        button_label = "Use Default Rate (0.20)"
    else:
        mutation_rate = 0.20
        st.success("Active mutation rate: 0.20 — Default")
        button_label = "Use Custom Rate (0.01–0.05)"

    # This single button is placed below the rate display/slider.
    # Default mode hides the custom slider; custom mode shows it.
    st.button(
        button_label,
        on_click=toggle_mutation_mode,
        use_container_width=True,
        help="Switch between the default mutation rate (0.20) and the custom slider (0.01–0.05).",
    )

if st.button("Generate Schedule", type="primary"):
    best_schedule = genetic_algorithm(ratings, crossover_rate, mutation_rate)
    fitness = fitness_function(best_schedule, ratings)

    schedule_table = []
    for index, program in enumerate(best_schedule):
        schedule_table.append(
            {
                "Time": f"{all_time_slots[index]:02d}:00",
                "Program": program,
                "Rating": round(ratings[program][index], 2),
            }
        )

    st.session_state.last_result = {
        "schedule": schedule_table,
        "fitness": round(fitness, 3),
        "crossover": crossover_rate,
        "mutation": mutation_rate,
    }

    trial_number = len(st.session_state.trial_history) + 1
    st.session_state.trial_history.append(
        {
            "Trial": trial_number,
            "CO_R": crossover_rate,
            "MUT_R": mutation_rate,
            "Fitness": round(fitness, 3),
        }
    )

if st.session_state.last_result is not None:
    result = st.session_state.last_result
    st.subheader("Generated TV Schedule")
    st.write(
        f"CO_R: **{result['crossover']:.2f}** | "
        f"MUT_R: **{result['mutation']:.2f}** | "
        f"Total Rating: **{result['fitness']:.3f}**"
    )
    st.table(result["schedule"])

if st.session_state.trial_history:
    st.subheader("Trial History")
    st.table(st.session_state.trial_history)
    st.caption("The assignment requires three trial runs with different rate combinations.")
