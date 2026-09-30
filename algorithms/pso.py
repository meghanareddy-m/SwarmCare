import random


class Particle:
    """
    Represents one candidate patient-priority solution.

    Each particle contains a continuous position vector.
    The ordering of patients is obtained by sorting the
    vector values.
    """

    def __init__(self, dimension, rng=None):
        """
        Initialize a particle using the supplied random
        number generator.

        A dedicated RNG is used so that PSO experiments
        are reproducible when the same seed is supplied.
        """

        if rng is None:
            rng = random.Random()

        self.position = [
            rng.uniform(0.0, 1.0)
            for _ in range(dimension)
        ]

        self.velocity = [
            rng.uniform(-0.2, 0.2)
            for _ in range(dimension)
        ]

        self.best_position = list(
            self.position
        )

        self.best_fitness = float("-inf")


class PatientPSO:
    """
    Particle Swarm Optimization for patient allocation.

    The PSO searches for an ordering of waiting patients.

    Parameters:
        swarm_size
        iterations
        inertia
        cognitive
        social
        seed
    """

    def __init__(
        self,
        swarm_size=12,
        iterations=15,
        inertia=0.7,
        cognitive=1.4,
        social=1.4,
        seed=42
    ):
        self.swarm_size = swarm_size
        self.iterations = iterations
        self.inertia = inertia
        self.cognitive = cognitive
        self.social = social
        self.seed = seed

        # Dedicated seeded RNG for complete reproducibility.
        self.rng = random.Random(seed)

        self.convergence = []

    # ======================================================
    # POSITION → PATIENT ORDER
    # ======================================================

    def decode_order(
        self,
        particle,
        patients
    ):
        """
        Convert a continuous PSO position into
        a discrete patient ordering.

        Smaller position values receive earlier priority.
        """

        indexed = list(
            enumerate(particle.position)
        )

        indexed.sort(
            key=lambda item: item[1]
        )

        return [
            patients[index]
            for index, _ in indexed
        ]

    # ======================================================
    # RESOURCE FEASIBILITY
    # ======================================================

    def evaluate_order(
        self,
        order,
        simulator
    ):
        """
        Evaluate a candidate patient ordering.

        This is a lightweight virtual evaluation.
        The real simulator state is not modified.

        The function estimates how many patients could
        be admitted with the currently available resources.
        """

        # ----------------------------------------------
        # Current resource occupation
        # ----------------------------------------------

        occupied_icu = sum(
            1
            for patient in simulator.treatment_patients()
            if patient.assigned_bed == "ICU"
        )

        occupied_ward = sum(
            1
            for patient in simulator.treatment_patients()
            if patient.assigned_bed == "WARD"
        )

        occupied_oxygen = sum(
            1
            for patient in simulator.treatment_patients()
            if patient.oxygen_required
        )

        occupied_ventilators = sum(
            1
            for patient in simulator.treatment_patients()
            if patient.ventilator_required
        )

        icu_available = max(
            0,
            simulator.icu_beds - occupied_icu
        )

        ward_available = max(
            0,
            simulator.ward_beds - occupied_ward
        )

        oxygen_available = max(
            0,
            simulator.oxygen - occupied_oxygen
        )

        ventilators_available = max(
            0,
            simulator.ventilators - occupied_ventilators
        )

        doctors_available = sum(
            1
            for doctor in simulator.doctors
            if doctor.available
            and doctor.current_load == 0
        )

        # ----------------------------------------------
        # Simulated allocation
        # ----------------------------------------------

        treated = 0
        critical_treated = 0
        conflicts = 0
        waiting_penalty = 0.0

        for patient in order:

            if doctors_available <= 0:
                conflicts += 1
                waiting_penalty += patient.waiting_time
                continue

            needs_icu = (
                patient.severity >= 0.80
            )

            needs_oxygen = (
                patient.oxygen_required
            )

            needs_ventilator = (
                patient.ventilator_required
            )

            # ------------------------------------------
            # Feasibility checks
            # ------------------------------------------

            if needs_icu:

                if icu_available <= 0:
                    conflicts += 1
                    waiting_penalty += (
                        patient.waiting_time
                    )
                    continue

            else:

                if ward_available <= 0:
                    conflicts += 1
                    waiting_penalty += (
                        patient.waiting_time
                    )
                    continue

            if (
                needs_oxygen
                and oxygen_available <= 0
            ):
                conflicts += 1
                waiting_penalty += (
                    patient.waiting_time
                )
                continue

            if (
                needs_ventilator
                and ventilators_available <= 0
            ):
                conflicts += 1
                waiting_penalty += (
                    patient.waiting_time
                )
                continue

            # ------------------------------------------
            # Simulated allocation
            # ------------------------------------------

            doctors_available -= 1

            if needs_icu:
                icu_available -= 1
            else:
                ward_available -= 1

            if needs_oxygen:
                oxygen_available -= 1

            if needs_ventilator:
                ventilators_available -= 1

            treated += 1

            if patient.severity >= 0.80:
                critical_treated += 1

        # ----------------------------------------------
        # Candidate fitness
        # ----------------------------------------------

        total_patients = max(
            len(order),
            1
        )

        critical_patients = sum(
            patient.severity >= 0.80
            for patient in order
        )

        critical_coverage = (
            critical_treated
            / max(
                critical_patients,
                1
            )
        )

        treatment_rate = (
            treated
            / total_patients
        )

        conflict_rate = (
            conflicts
            / total_patients
        )

        waiting_penalty = min(
            waiting_penalty
            / total_patients
            / 20.0,
            1.0
        )

        fitness = (
            0.45 * critical_coverage
            + 0.35 * treatment_rate
            - 0.10 * conflict_rate
            - 0.10 * waiting_penalty
        )

        return fitness

    # ======================================================
    # OPTIMIZE
    # ======================================================

    def optimize(
        self,
        patients,
        simulator
    ):
        """
        Run PSO and return the best patient ordering.
        """

        # Reset convergence for each optimization run.
        self.convergence = []

        if not patients:
            return [], {
                "best_fitness": 0.0,
                "iterations": 0,
                "convergence": []
            }

        dimension = len(patients)

        # Every particle receives the same dedicated seeded
        # RNG owned by this PSO instance. Random calls are
        # therefore deterministic for a given seed.
        particles = [
            Particle(
                dimension,
                rng=self.rng
            )
            for _ in range(self.swarm_size)
        ]

        # ----------------------------------------------
        # Initialize global best
        # ----------------------------------------------

        global_best_position = None
        global_best_fitness = float("-inf")

        # ----------------------------------------------
        # Main PSO loop
        # ----------------------------------------------

        for iteration in range(
            self.iterations
        ):

            for particle in particles:

                order = self.decode_order(
                    particle,
                    patients
                )

                fitness = self.evaluate_order(
                    order,
                    simulator
                )

                # --------------------------------------
                # Personal best
                # --------------------------------------

                if (
                    fitness
                    > particle.best_fitness
                ):
                    particle.best_fitness = (
                        fitness
                    )

                    particle.best_position = list(
                        particle.position
                    )

                # --------------------------------------
                # Global best
                # --------------------------------------

                if (
                    fitness
                    > global_best_fitness
                ):
                    global_best_fitness = (
                        fitness
                    )

                    global_best_position = list(
                        particle.position
                    )

            # Global best can only improve or remain equal.
            self.convergence.append(
                global_best_fitness
            )

            # ------------------------------------------
            # Update particles
            # ------------------------------------------

            for particle in particles:

                for i in range(dimension):

                    # IMPORTANT:
                    # Always use the seeded RNG.
                    r1 = self.rng.random()
                    r2 = self.rng.random()

                    cognitive_term = (
                        self.cognitive
                        * r1
                        * (
                            particle.best_position[i]
                            - particle.position[i]
                        )
                    )

                    social_term = (
                        self.social
                        * r2
                        * (
                            global_best_position[i]
                            - particle.position[i]
                        )
                    )

                    particle.velocity[i] = (
                        self.inertia
                        * particle.velocity[i]
                        + cognitive_term
                        + social_term
                    )

                    # Limit velocity for stability.
                    particle.velocity[i] = max(
                        -0.5,
                        min(
                            0.5,
                            particle.velocity[i]
                        )
                    )

                    particle.position[i] += (
                        particle.velocity[i]
                    )

                    # Keep position bounded.
                    particle.position[i] = max(
                        0.0,
                        min(
                            1.0,
                            particle.position[i]
                        )
                    )

        # ----------------------------------------------
        # Decode final solution
        # ----------------------------------------------

        best_particle = Particle(
            dimension,
            rng=self.rng
        )

        best_particle.position = list(
            global_best_position
        )

        best_order = self.decode_order(
            best_particle,
            patients
        )

        return best_order, {
            "best_fitness":
                global_best_fitness,

            "iterations":
                self.iterations,

            "convergence":
                list(self.convergence)
        }