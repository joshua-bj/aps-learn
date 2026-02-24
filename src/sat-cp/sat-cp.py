"""
简单的约束规划（CP-SAT）示例 - 查找多个解

本示例展示如何使用 OR-Tools CP-SAT 求解器查找一个问题的多个解。
每次找到一个解后，添加约束排除该解，继续查找下一个解。
"""
from ortools.sat.python import cp_model


class VarArraySolutionPrinter(cp_model.CpSolverSolutionCallback):
    """打印并收集所有解的回调函数类"""

    def __init__(self, variables, limit=10):
        """初始化回调函数

        Args:
            variables: 需要打印值的变量列表
            limit: 最大解的数量限制，默认为10
        """
        cp_model.CpSolverSolutionCallback.__init__(self)
        self.__variables = variables
        self.__solution_count = 0
        self.__solutions = []  # 存储所有找到的解
        self.__limit = limit  # 解的数量上限

    def on_solution_callback(self):
        """每次找到解时被调用"""
        self.__solution_count += 1

        # 收集当前解的值
        solution = []
        for var in self.__variables:
            solution.append(self.value(var))

        self.__solutions.append(solution)

        # 打印当前解
        print(f"解 {self.__solution_count}:")
        for i, var in enumerate(self.__variables):
            print(f"  {var.name} = {solution[i]}")
        print()

        # 如果达到解的数量上限，停止搜索
        if self.__solution_count >= self.__limit:
            self.StopSearch()

    def solution_count(self):
        """返回已找到的解的数量"""
        return self.__solution_count

    def solutions(self):
        """返回所有找到的解"""
        return self.__solutions


def simple_sat_program_multiple_solutions():
    """CP-SAT 示例：查找多个可行解"""
    # ==================== 创建模型 ====================
    model = cp_model.CpModel()

    # ==================== 创建变量 ====================
    # 创建三个整数变量，取值范围都是 [0, 2]
    num_vals = 3
    x = model.new_int_var(0, num_vals - 1, "x")
    y = model.new_int_var(0, num_vals - 1, "y")
    z = model.new_int_var(0, num_vals - 1, "z")

    # ==================== 添加约束条件 ====================
    # 约束：x 和 y 不能相等
    model.add(x != y)

    # ==================== 创建求解器并设置参数 ====================
    solver = cp_model.CpSolver()

    # 设置求解器参数以查找所有解
    # enumerate_all_solutions: 枚举所有可行解的关键参数
    solver.parameters.enumerate_all_solutions = True
    solver.parameters.num_search_workers = 1  # 使用单线程以保证解的顺序

    # ==================== 创建回调函数 ====================
    # 将所有变量放入列表，方便后续处理
    variables = [x, y, z]
    # 创建回调函数，限制最多查找10个解
    solution_printer = VarArraySolutionPrinter(variables, limit=10)

    # ==================== 求解模型 ====================
    # 使用回调函数进行求解
    status = solver.solve(model, solution_printer)

    # ==================== 输出统计信息 ====================
    print(f"\n搜索完成！共找到 {solution_printer.solution_count()} 个解")
    print(f"求解状态: {solver.status_name(status)}")
    print(f"冲突次数: {solver.num_conflicts}")
    print(f"分支次数: {solver.num_branches}")
    print(f"耗时: {solver.wall_time} 秒")


def simple_sat_program_iterative():
    """
    CP-SAT 示例：通过迭代方式查找多个解

    这种方法每次找到一个解后，添加约束排除该解，然后重新求解。
    这样可以系统地遍历所有可能的解。
    """
    # ==================== 创建模型 ====================
    model = cp_model.CpModel()

    # ==================== 创建变量 ====================
    num_vals = 3
    x = model.new_int_var(0, num_vals - 1, "x")
    y = model.new_int_var(0, num_vals - 1, "y")
    z = model.new_int_var(0, num_vals - 1, "z")

    # ==================== 添加约束条件 ====================
    model.add(x != y)

    # 创建求解器
    solver = cp_model.CpSolver()

    # 存储所有变量
    variables = [x, y, z]

    # ==================== 迭代查找多个解 ====================
    max_solutions = 10  # 最多查找10个解
    solution_count = 0

    print(f"开始查找最多 {max_solutions} 个解：\n")

    for i in range(max_solutions):
        # 求解当前模型
        status = solver.solve(model)

        # 如果没有找到可行解，停止搜索
        if status != cp_model.OPTIMAL and status != cp_model.FEASIBLE:
            print("\n没有更多解了。")
            break

        # 打印当前解
        solution_count += 1
        print(f"解 {solution_count}:")
        for var in variables:
            print(f"  {var.name} = {solver.value(var)}")
        print()

        # 添加约束以排除当前解，确保下次找到不同的解
        # 方法：添加约束，要求至少有一个变量不等于当前解中的值
        # 使用布尔变量和枚举来实现
        exclusion_constraints = []
        for var in variables:
            current_value = solver.value(var)
            # 创建一个布尔变量，表示 var 是否等于当前值
            is_equal = model.new_bool_var(f"is_equal_{var.name}_{i}")
            # 约束：当 is_equal 为 True 时，var 必须等于当前值
            model.add(var == current_value).only_enforce_if(is_equal)
            # 约束：当 is_equal 为 False 时，var 必须不等于当前值
            model.add(var != current_value).only_enforce_if(is_equal.Not())
            exclusion_constraints.append(is_equal)

        # 约束：至少有一个变量不等于当前解中的值
        # 即：排除当前解
        model.add_bool_or([c.Not() for c in exclusion_constraints])

    # ==================== 输出统计信息 ====================
    print(f"搜索完成！共找到 {solution_count} 个解")


# 运行示例
if __name__ == "__main__":
    print("=" * 60)
    print("方法1：使用回调函数查找多个解")
    print("=" * 60)
    simple_sat_program_multiple_solutions()

    print("\n" + "=" * 60)
    print("方法2：使用迭代方式查找多个解")
    print("=" * 60)
    simple_sat_program_iterative()