from ortools.linear_solver import pywraplp

def lp_example():
    solver = pywraplp.Solver.CreateSolver("GLOP")

    x = solver.NumVar(0, solver.infinity(), "x")
    y = solver.NumVar(0, solver.infinity(), "y")
    z = solver.NumVar(0, solver.infinity(), "z")



    solver.Add(x*0.02+y*0.03+z*0.05<=40)
    solver.Add(x*0.05+y*0.02+z*0.04<=40)

    solver.Maximize(50*x+40*y+30*z)

    status = solver.Solve()

    if status == pywraplp.Solver.OPTIMAL:
        print("Optimal solution:")
        print("x =", x.solution_value())
        print("y =", y.solution_value())
        print("z =", z.solution_value())
        print("Max profit =", solver.Objective().Value())

lp_example()