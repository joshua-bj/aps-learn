from ortools.linear_solver import pywraplp

def lp_example():
    solver = pywraplp.Solver.CreateSolver("GLOP")

    x = solver.NumVar(0, solver.infinity(), "x")
    y = solver.NumVar(0, solver.infinity(), "y")

    solver.Add(3*x+2*y<=2400)
    solver.Add(y<=800)
    solver.Add(2*x<=1200)

    solver.Maximize(100*x+40*y)

    status = solver.Solve()

    if status == pywraplp.Solver.OPTIMAL:
        print("Optimal solution:")
        print("x =", x.solution_value())
        print("y =", y.solution_value())
        print("Max profit =", solver.Objective().Value())

lp_example()