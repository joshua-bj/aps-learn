from ortools.linear_solver import pywraplp

def lp_example():
    solver = pywraplp.Solver.CreateSolver("GLOP")

    x = solver.NumVar(0, solver.infinity(), "x")
    y = solver.NumVar(0, solver.infinity(), "y")

    solver.Add(2 * x + y <= 100)
    solver.Add(x + 2 * y <= 80)

    solver.Maximize(3 * x + 4 * y)

    status = solver.Solve()

    if status == pywraplp.Solver.OPTIMAL:
        print("Optimal solution:")
        print("x =", x.solution_value())
        print("y =", y.solution_value())
        print("Max profit =", solver.Objective().Value())

lp_example()