import bisect

# Shared predefined array (10 values)
shared_array = [42, 7, 19, 88, 3, 55, 24, 61, 10, 31]
shared_array.sort()

print("Initial sorted array:")
print(shared_array)
print("=" * 50)

# Agent class
class Agent:
    def __init__(self, agent_id):
        self.id = agent_id

    def insert_value(self, value):
        bisect.insort(shared_array, value)
        print(f"Agent {self.id} inserted {value}")

    def remove_value(self, value):
        if value in shared_array:
            shared_array.remove(value)
            print(f"Agent {self.id} removed {value}")
        else:
            print(f"Value {value} not found in array")


# Create 3 agents
agents = {
    1: Agent(1),
    2: Agent(2),
    3: Agent(3)
}

# Interactive simulation loop
while True:
    print("\nCurrent array:", shared_array)

    print("\nChoose an agent (1, 2, 3) or 0 to exit:")
    agent_choice = int(input("Agent: "))

    if agent_choice == 0:
        print("Simulation ended.")
        break

    if agent_choice not in agents:
        print("Invalid agent number.")
        continue

    print("Choose operation:")
    print("1 → Insert")
    print("2 → Remove")
    operation = int(input("Operation: "))

    if operation == 1:
        value = int(input("Enter value to insert: "))
        agents[agent_choice].insert_value(value)

    elif operation == 2:
        value = int(input("Enter value to remove: "))
        agents[agent_choice].remove_value(value)

    else:
        print("Invalid operation.")

    print("Updated sorted array:", shared_array)
    print("-" * 50)