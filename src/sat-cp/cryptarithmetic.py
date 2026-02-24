"""Cryptarithmetic puzzle.
算术谜题。

First attempt to solve equation CP + IS + FUN = TRUE
首次尝试求解方程 CP + IS + FUN = TRUE

where each letter represents a unique digit.
其中每个字母代表一个唯一的数字。

This problem has 72 different solutions in base 10.
这个问题在十进制下有72个不同的解。
"""

# 从 ortools 库导入约束编程（CP）模块
# ortools 是 Google 开源的一套优化工具，cp_model 是约束编程求解器
from ortools.sat.python import cp_model


# 定义一个解决方案打印器类，继承自 CpSolverSolutionCallback
# 这是一个回调类，用于在求解器找到每个解时自动调用
class VarArraySolutionPrinter(cp_model.CpSolverSolutionCallback):
    """Print intermediate solutions."""
    """打印中间解决方案（每个找到的解都会打印）。"""

    # 类的构造函数（初始化方法），在创建对象时自动调用
    # variables: 一个 IntVar 变量列表，表示我们要打印的变量
    def __init__(self, variables: list[cp_model.IntVar]):
        # 调用父类的初始化方法（必须这样做）
        cp_model.CpSolverSolutionCallback.__init__(self)
        # 将变量列表保存到实例变量 __variables 中（双下划线表示私有变量）
        self.__variables = variables
        # 初始化解的计数器为 0
        self.__solution_count = 0

    # 当求解器找到一个解时，会自动调用这个方法
    def on_solution_callback(self) -> None:
        # 解的数量加 1
        self.__solution_count += 1
        # 遍历所有变量
        for v in self.__variables:
            # 打印变量名和它的值，self.value(v) 获取变量 v 在当前解中的值
            # end=" " 表示打印后不换行，而是加一个空格
            print(f"{v}={self.value(v)}", end=" ")
        # 打印完所有变量后换行
        print()

    # @property 是一个装饰器，让我们可以像访问属性一样访问这个方法
    # 即：solution_count 而不是 solution_count()
    @property
    def solution_count(self) -> int:
        # 返回找到的解的总数
        return self.__solution_count


# 主函数，程序的入口点
def main() -> None:
    """solve the CP+IS+FUN==TRUE cryptarithm."""
    """求解 CP+IS+FUN==TRUE 这个算术谜题。"""

    # ========== 步骤1: 创建约束编程模型 ==========
    # CpModel() 是约束编程模型，用于定义变量和约束
    model = cp_model.CpModel()

    # 定义进制数（这里是十进制，所以 base = 10）
    base = 10

    # ========== 步骤2: 创建变量 ==========
    # new_int_var(最小值, 最大值, 名称) 创建一个整数变量
    # 首字母（C, I, F, T）的范围是 1-9（不能为0，因为是一个数的首位）
    # 其他字母的范围是 0-9

    c = model.new_int_var(1, base - 1, "C")  # C ∈ [1, 9]，表示 CP 的十位
    p = model.new_int_var(0, base - 1, "P")  # P ∈ [0, 9]，表示 CP 的个位
    i = model.new_int_var(1, base - 1, "I")  # I ∈ [1, 9]，表示 IS 的十位
    s = model.new_int_var(0, base - 1, "S")  # S ∈ [0, 9]，表示 IS 的个位
    f = model.new_int_var(1, base - 1, "F")  # F ∈ [1, 9]，表示 FUN 的百位
    u = model.new_int_var(0, base - 1, "U")  # U ∈ [0, 9]，表示 FUN 的十位
    n = model.new_int_var(0, base - 1, "N")  # N ∈ [0, 9]，表示 FUN 的个位
    t = model.new_int_var(1, base - 1, "T")  # T ∈ [1, 9]，表示 TRUE 的千位
    r = model.new_int_var(0, base - 1, "R")  # R ∈ [0, 9]，表示 TRUE 的百位
    e = model.new_int_var(0, base - 1, "E")  # E ∈ [0, 9]，表示 TRUE 的个位

    # ========== 步骤3: 将变量放入列表 ==========
    # 把所有字母变量放入一个列表，方便后续使用
    # AllDifferent 约束需要一个列表作为参数
    letters = [c, p, i, s, f, u, n, t, r, e]

    # 断言：确保进制数大于等于字母的数量
    # assert 是一个调试语句，如果条件为 False，程序会报错
    # 这里检查是否有足够的数字（0-9）来分配给所有字母
    assert base >= len(letters)  # 10 >= 10，成立

    # ========== 步骤4: 添加约束 ==========
    # 添加 "所有字母互不相同" 的约束
    # 即：C, P, I, S, F, U, N, T, R, E 这10个字母必须代表10个不同的数字
    model.add_all_different(letters)

    # 添加算术方程约束：CP + IS + FUN = TRUE
    # 这里将字母转换为数值：
    # CP = C * 10 + P（两位数）
    # IS = I * 10 + S（两位数）
    # FUN = F * 100 + U * 10 + N（三位数）
    # TRUE = T * 1000 + R * 100 + U * 10 + E（四位数）
    #
    # 方程展开：
    #   (10*C + P) + (10*I + S) + (100*F + 10*U + N) = 1000*T + 100*R + 10*U + E
    model.add(
        c * base + p + i * base + s + f * base * base + u * base + n
        == t * base * base * base + r * base * base + u * base + e
    )

    # ========== 步骤5: 创建求解器并求解 ==========
    # 创建一个 CP-SAT 求解器实例
    solver = cp_model.CpSolver()

    # 创建一个解决方案打印器对象，传入字母变量列表
    solution_printer = VarArraySolutionPrinter(letters)

    # 设置求解器参数：枚举所有解（而不只是找到一个解就停止）
    solver.parameters.enumerate_all_solutions = True

    # 开始求解模型，传入 solution_printer 作为回调函数
    # 每找到一个解，就会调用 solution_printer.on_solution_callback()
    status = solver.solve(model, solution_printer)

    # ========== 步骤6: 打印统计信息 ==========
    print("\nStatistics")  # 打印标题 "统计信息"
    # 打印求解状态（OPTIMAL, FEASIBLE, INFEASIBLE 等）
    print(f"  status   : {solver.status_name(status)}")
    # 打印冲突次数（求解器在搜索过程中遇到的约束冲突次数）
    print(f"  conflicts: {solver.num_conflicts}")
    # 打印分支次数（求解器搜索决策树时的分支数量）
    print(f"  branches : {solver.num_branches}")
    # 打印求解耗时（单位：秒）
    print(f"  wall time: {solver.wall_time} s")
    # 打印找到的解的总数
    print(f"  sol found: {solution_printer.solution_count}")


# 这是 Python 的特殊写法
# 如果这个文件被直接运行（而不是被其他文件导入），则执行下面的代码
# __name__ 是 Python 的内置变量，直接运行时值为 "__main__"
if __name__ == "__main__":
    main()  # 调用主函数
