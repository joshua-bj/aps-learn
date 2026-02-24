"""简单的护士排班问题示例。"""
# 导入 Google OR-Tools 的 CP-SAT 约束规划求解器
# CP-SAT 是一个高效的约束满足问题求解器，用于解决组合优化问题
from ortools.sat.python import cp_model


def main() -> None:
    # ============ 数据定义 ============
    # 护士数量
    num_nurses = 4
    # 班次数量（例如：早班、中班、晚班）
    num_shifts = 3
    # 排班天数
    num_days = 3
    # 创建护士索引范围：0, 1, 2, 3
    all_nurses = range(num_nurses)
    # 创建班次索引范围：0, 1, 2
    all_shifts = range(num_shifts)
    # 创建天数索引范围：0, 1, 2
    all_days = range(num_days)

    # ============ 创建约束规划模型 ============
    # CpModel() 是 CP-SAT 求解器的核心模型类
    model = cp_model.CpModel()

    # ============ 创建决策变量 ============
    # shifts[(n, d, s)] 是一个布尔变量：
    # - True 表示护士 n 在第 d 天的第 s 个班次工作
    # - False 表示该护士不在该班次工作
    # 这里的 (n, d, s) 是字典的键，用于唯一标识每个变量
    shifts = {}
    for n in all_nurses:
        for d in all_days:
            for s in all_shifts:
                # new_bool_var() 创建一个布尔变量（0 或 1）
                # 变量名称格式：shift_n0_d0_s0 表示护士0在第0天的第0班次
                shifts[(n, d, s)] = model.new_bool_var(f"shift_n{n}_d{d}_s{s}")

    # ============ 添加约束条件 ============

    # 约束1：每个班次每天必须恰好分配给一名护士
    # add_exactly_one() 确保给定的变量列表中恰好有一个为 True
    for d in all_days:
        for s in all_shifts:
            # 对于每一天的每个班次，所有护士中必须有一人上班
            model.add_exactly_one(shifts[(n, d, s)] for n in all_nurses)

    # 约束2：每个护士每天最多只能上一个班次
    # add_at_most_one() 确保给定的变量列表中最多有一个为 True（可以全为 False）
    for n in all_nurses:
        for d in all_days:
            # 对于每个护士的每一天，所有班次中最多上一个班次
            model.add_at_most_one(shifts[(n, d, s)] for s in all_shifts)

    # 约束3：尽量平均分配班次给每个护士
    # 计算每个护士应该工作的最少班次数
    # 使用整数除法 // 向下取整
    # 总班次数 = 3天 × 3班次 = 9个班次
    # 平均每个护士 = 9 ÷ 4 = 2.25，所以最少是 2 个班次
    min_shifts_per_nurse = (num_shifts * num_days) // num_nurses

    # 判断总班次是否能被护士数量整除
    if num_shifts * num_days % num_nurses == 0:
        # 如果能整除，最大班次等于最小班次（完全平均）
        max_shifts_per_nurse = min_shifts_per_nurse
    else:
        # 如果不能整除，部分护士会多上一个班次
        max_shifts_per_nurse = min_shifts_per_nurse + 1

    # 为每个护士添加班次数量的约束
    for n in all_nurses:
        shifts_worked = []
        # 收集该护士在所有天、所有班次的变量
        for d in all_days:
            for s in all_shifts:
                shifts_worked.append(shifts[(n, d, s)])
        # sum() 对布尔变量求和，True 计为 1，False 计为 0
        # 确保每个护士工作的班次数在最小值和最大值之间
        model.add(min_shifts_per_nurse <= sum(shifts_worked))
        model.add(sum(shifts_worked) <= max_shifts_per_nurse)

    # ============ 创建求解器并配置参数 ============
    # CpSolver 是 CP-SAT 求解器的主要类
    solver = cp_model.CpSolver()

    # linearization_level: 线性化级别
    # 0 表示不进行线性化，保持约束的原始形式
    solver.parameters.linearization_level = 0

    # enumerate_all_solutions: 枚举所有解
    # True 表示查找所有可能的可行解，而不是只找一个最优解
    solver.parameters.enumerate_all_solutions = True

    # ============ 定义解决方案回调类 ============
    # CpSolverSolutionCallback 是一个基类，用于在求解过程中处理每个找到的解
    class NursesPartialSolutionPrinter(cp_model.CpSolverSolutionCallback):
        """打印中间解决方案的回调类。"""

        def __init__(self, shifts, num_nurses, num_days, num_shifts, limit):
            # 调用父类的初始化方法
            cp_model.CpSolverSolutionCallback.__init__(self)
            # 保存排班变量的引用
            self._shifts = shifts
            # 保存护士数量
            self._num_nurses = num_nurses
            # 保存天数
            self._num_days = num_days
            # 保存班次数量
            self._num_shifts = num_shifts
            # 已找到的解的计数器
            self._solution_count = 0
            # 最大解的数量限制
            self._solution_limit = limit

        # 当求解器找到一个解时，会自动调用这个方法
        def on_solution_callback(self):
            # 增加解的计数
            self._solution_count += 1
            print(f"Solution {self._solution_count}")

            # 遍历每一天
            for d in range(self._num_days):
                print(f"Day {d}")
                # 遍历每个护士
                for n in range(self._num_nurses):
                    is_working = False
                    # 检查该护士在该天的每个班次是否工作
                    for s in range(self._num_shifts):
                        # self.value() 获取变量在当前解中的值（True 或 False）
                        if self.value(self._shifts[(n, d, s)]):
                            is_working = True
                            print(f"  Nurse {n} works shift {s}")
                    # 如果该护士当天任何班次都不工作
                    if not is_working:
                        print(f"  Nurse {n} does not work")

            # 如果找到的解数量达到限制，停止搜索
            if self._solution_count >= self._solution_limit:
                print(f"Stop search after {self._solution_limit} solutions")
                # stop_search() 告诉求解器停止寻找更多的解
                self.stop_search()

        # 返回已找到的解的数量
        def solutionCount(self):
            return self._solution_count

    # ============ 创建回调对象并求解 ============
    # 显示前 5 个解决方案
    solution_limit = 5
    # 创建回调对象，传入排班变量和各种参数
    solution_printer = NursesPartialSolutionPrinter(
        shifts, num_nurses, num_days, num_shifts, solution_limit
    )

    # solve() 方法开始求解
    # 传入 model 和 solution_printer，求解器会在找到解时调用回调
    solver.solve(model, solution_printer)

    # ============ 输出求解统计信息 ============
    print("\nStatistics")
    # num_conflicts: 求解过程中遇到的冲突数量（约束传播产生的冲突）
    print(f"  - conflicts      : {solver.num_conflicts}")
    # num_branches: 搜索树中的分支数量（回溯算法的分支决策次数）
    print(f"  - branches       : {solver.num_branches}")
    # wall_time: 实际求解耗时（单位：秒）
    print(f"  - wall time      : {solver.wall_time} s")
    # solutions found: 找到的解的总数量
    print(f"  - solutions found: {solution_printer.solutionCount()}")


# Python 的标准入口点检查
# 如果这个脚本被直接运行（而不是被导入），则执行 main() 函数
if __name__ == "__main__":
    main()