import simpy
import random

class Patient:
      def __init__(self, name, preparation_time, operation_time, recovery_time):
        self.name = name
        self.preparation_time = preparation_time
        self.operation_time = operation_time
        self.recovery_time = recovery_time
        
def patient_generator(env, patient_count, preparation_units, operating_theater, recovery_units):
   for i in range(patient_count):
        patient = Patient(name=f'Patient_{i}', 
                          preparation_time=random.expovariate(1/preparation_units.capacity),
                          operation_time=random.expovariate(1),
                          recovery_time=random.expovariate(1/recovery_units.capacity))
        env.process(patient_process(env, patient, preparation_units, operating_theater, recovery_units))
        yield env.timeout(random.expovariate(1/25))  # Interarrival time

def patient_process(env, patient, preparation_units, operating_theater, recovery_units):
    # Patient arrives and waits for a preparatory facility
    with preparation_units.request() as req:
        yield req
        yield env.timeout(patient.preparation_time)

    # Move to the operating theater
    with operating_theater.request() as req:
        yield req
        yield env.timeout(patient.operation_time)

    # Wait for a recovery facility
    with recovery_units.request() as req:
        yield req
        yield env.timeout(patient.recovery_time)

    # Departure
    print(f'{patient.name} has completed the process at time {env.now}')

def monitor_system(env, preparation_units, operating_theater, recovery_units, data_collection_interval, max_simulation_time):
    queue_lengths = []
    theater_utilizations = []

    while True:
        # Observe and collect data
        queue_lengths.append(len(preparation_units.queue))
        theater_utilizations.append(operating_theater.count / operating_theater.capacity)

        # Check if the simulation time has reached the maximum specified time
        if env.now >= max_simulation_time:
            break

        # Wait for the next observation interval
        yield env.timeout(data_collection_interval)

    return queue_lengths, theater_utilizations

def simulation(env, patient_count, preparation_units, operating_theater, recovery_units, max_simulation_time):
    patient_gen = env.process(patient_generator(env, patient_count, preparation_units, operating_theater, recovery_units))
    yield patient_gen

# Setup
env = simpy.Environment()

# Resources
preparation_units = simpy.Resource(env, capacity=3)  # P identical preparation rooms
operating_theater = simpy.Resource(env, capacity=1)   # One operating theater
recovery_units = simpy.Resource(env, capacity=3)      # R recovery rooms

# Parameters
data_collection_interval = 5  # Adjust the monitoring interval as needed
max_simulation_time = 50

# Processes
env.process(simulation(env, patient_count=10, preparation_units=preparation_units, 
                       operating_theater=operating_theater, recovery_units=recovery_units,
                       max_simulation_time=max_simulation_time))
monitor_process = env.process(monitor_system(env, preparation_units, operating_theater, recovery_units, 
                                             data_collection_interval, max_simulation_time))

# Run the simulation
env.run()

# Access monitoring results
queue_lengths, theater_utilizations = monitor_process.value
print(f'Queue Lengths: {queue_lengths}')
print(f'Theater Utilizations: {theater_utilizations}')
