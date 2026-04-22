from ortools.sat.python import cp_model
import random

# -------------------------
# 1. 数据生成
# -------------------------

random.seed(0)

NUM_JOBS = 100
NUM_MACHINES = 5
OPS_PER_JOB = 3

# 每个订单的工艺路线 (随机机器)
routes = [
    [random.randint(0, NUM_MACHINES - 1) for _ in range(OPS_PER_JOB)]
    for _ in range(NUM_JOBS)
]

# 每道工序加工时间
durations = [
    [random.randint(5, 20) for _ in range(OPS_PER_JOB)]
    for _ in range(NUM_JOBS)
]

# 订单交期
due_dates = [
    random.randint(150, 300)
    for _ in range(NUM_JOBS)
]

penalties = [random.randint(1, 5) for _ in range(NUM_JOBS)]

# horizon = 所有加工时间总和
horizon = sum(sum(durations[i]) for i in range(NUM_JOBS))

# -------------------------
# 2. 建立模型
# -------------------------

model = cp_model.CpModel()

all_tasks = {}
machine_to_intervals = {m: [] for m in range(NUM_MACHINES)}

# -------------------------
# 3. 创建变量（使用宽松边界）
# -------------------------
# 注意：紧域计算在大规模问题中过于严格，可能导致不可行
# 这里使用 horizon 作为边界，让求解器自动寻找最优解

for i in range(NUM_JOBS):
    for k in range(OPS_PER_JOB):
        duration = durations[i][k]
        machine = routes[i][k]

        # 使用 [0, horizon] 作为边界
        start = model.NewIntVar(0, horizon, f"start_{i}_{k}")
        end = model.NewIntVar(0, horizon, f"end_{i}_{k}")
        interval = model.NewIntervalVar(start, duration, end, f"interval_{i}_{k}")

        all_tasks[(i, k)] = (start, end, interval)
        machine_to_intervals[machine].append(interval)

# -------------------------
# 4. 工艺顺序约束
# -------------------------

for i in range(NUM_JOBS):
    for k in range(OPS_PER_JOB - 1):
        _, end1, _ = all_tasks[(i, k)]
        start2, _, _ = all_tasks[(i, k + 1)]
        model.Add(end1 <= start2)

# -------------------------
# 5. 机器资源约束
# -------------------------

for m in range(NUM_MACHINES):
    model.AddNoOverlap(machine_to_intervals[m])

# -------------------------
# 6. 延期变量（使用 AddMaxEquality）
# -------------------------

lateness = []
objective_terms = []

for i in range(NUM_JOBS):
    _, end_last, _ = all_tasks[(i, OPS_PER_JOB - 1)]

    late = model.NewIntVar(0, horizon, f"lateness_{i}")

    # late = max(0, end_last - due_date)
    model.AddMaxEquality(late, [0, end_last - due_dates[i]])

    lateness.append(late)
    objective_terms.append(penalties[i] * late)

# -------------------------
# 7. 目标函数
# -------------------------

model.Minimize(sum(objective_terms))

# -------------------------
# 8. 求解参数
# -------------------------

solver = cp_model.CpSolver()
solver.parameters.max_time_in_seconds = 30
solver.parameters.num_search_workers = 8
solver.parameters.log_search_progress = True
solver.parameters.search_branching = cp_model.PORTFOLIO_SEARCH

# -------------------------
# 9. 求解
# -------------------------

status = solver.Solve(model)

# -------------------------
# 10. 输出结果
# -------------------------

if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
    print("Objective value:", solver.ObjectiveValue())

    for i in range(5):  # 只打印前5个订单
        print(f"\nJob {i}")
        for k in range(OPS_PER_JOB):
            start, end, _ = all_tasks[(i, k)]
            print(
                f"  Op{k} (M{routes[i][k]}) : "
                f"{solver.Value(start)} -> {solver.Value(end)}"
            )
else:
    print("No solution found.")