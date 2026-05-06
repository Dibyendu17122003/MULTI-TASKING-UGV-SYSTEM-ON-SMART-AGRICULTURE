def tower_of_hanoi(n, source, auxiliary, destination, moves):
    """
    Recursive function to solve Tower of Hanoi
    n          : number of disks
    source     : source rod
    auxiliary  : helper rod
    destination: destination rod
    moves      : list to store moves
    """

    if n == 1:
        moves.append(f"Move disk 1 from {source} to {destination}")
        return

    # Move n-1 disks from source to auxiliary
    tower_of_hanoi(n - 1, source, destination, auxiliary, moves)

    # Move largest disk to destination
    moves.append(f"Move disk {n} from {source} to {destination}")

    # Move n-1 disks from auxiliary to destination
    tower_of_hanoi(n - 1, auxiliary, source, destination, moves)


# ---------------- MAIN PROGRAM ---------------- #

# User input
n = int(input("Enter number of disks: "))

if n <= 0:
    print("Number of disks must be greater than 0.")
else:
    moves = []

    print("\nSolving Tower of Hanoi...\n")

    tower_of_hanoi(n, "A", "B", "C", moves)

    # Print all moves
    for step, move in enumerate(moves, start=1):
        print(f"Step {step}: {move}")

    print("\nTotal moves required:", len(moves))
