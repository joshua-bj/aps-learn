from ortools.linear_solver import pywraplp

def milp_example():
    solver = pywraplp.Solver.CreateSolver("CBC")

    A = solver.BoolVar("Factory_A")
    B = solver.BoolVar("Factory_B")

    solver.Add(A + B >= 1)

    solver.Minimize(10 * A + 6 * B)

    status = solver.Solve()

    if status == pywraplp.Solver.OPTIMAL:
        print("Optimal solution:")
        print("Factory A:", A.solution_value())
        print("Factory B:", B.solution_value())
        print("Minimum cost:", solver.Objective().Value())

milp_example()