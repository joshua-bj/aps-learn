"""OR-Tools solution to the N-queens problem."""
"""使用 OR-Tools 求解 N 皇后问题。"""

# 导入 sys 模块，用于获取命令行参数
import sys
# 导入 time 模块，用于计时
import time
# 从 ortools 库导入约束编程（CP）模块
from ortools.sat.python import cp_model


# N 皇后解决方案打印器类
# 继承自 CpSolverSolutionCallback，用于在找到每个解时自动调用
class NQueenSolutionPrinter(cp_model.CpSolverSolutionCallback):
    """Print intermediate solutions."""
    """打印中间解决方案（每个找到的解都会打印棋盘）。"""

    # 类的构造函数（初始化方法），在创建对象时自动调用
    # queens: 一个 IntVar 变量列表，表示每列中皇后的位置
    def __init__(self, queens: list[cp_model.IntVar]):
        # 调用父类的初始化方法（必须这样做）
        cp_model.CpSolverSolutionCallback.__init__(self)
        # 将皇后变量列表保存到实例变量 __queens 中（双下划线表示私有变量）
        self.__queens = queens
        # 初始化解的计数器为 0
        self.__solution_count = 0
        # 记录开始时间，用于计算求解耗时
        self.__start_time = time.time()

    # @property 装饰器，让我们可以像访问属性一样访问这个方法
    # 即：solution_count 而不是 solution_count()
    @property
    def solution_count(self) -> int:
        # 返回找到的解的总数
        return self.__solution_count

    # 当求解器找到一个解时，会自动调用这个方法
    def on_solution_callback(self):
        # 获取当前时间，用于计算这个解的求解耗时
        current_time = time.time()
        # 打印解的编号和耗时
        print(
            f"Solution {self.__solution_count}, "
            f"time = {current_time - self.__start_time} s"
        )
        # 解的数量加 1
        self.__solution_count += 1

        # 创建棋盘大小的范围（0 到 board_size-1）
        # range(len(self.__queens)) 生成 0, 1, 2, ..., board_size-1
        all_queens = range(len(self.__queens))

        # 打印棋盘：i 代表行，j 代表列
        for i in all_queens:  # 遍历每一行
            for j in all_queens:  # 遍历每一列
                # 检查第 j 列的皇后是否在第 i 行
                # self.value(self.__queens[j]) 获取第 j 列皇后的行号
                if self.value(self.__queens[j]) == i:
                    # 如果第 j 列的皇后在第 i 行，打印 "Q"（Queen）
                    print("Q", end=" ")
                else:
                    # 否则打印 "_"（空位）
                    print("_", end=" ")
            # 打印完一行后换行
            print()
        # 打印完整个棋盘后再空一行
        print()




# 主函数，求解 N 皇后问题
# board_size: 棋盘大小（默认是 8，表示 8×8 棋盘）
def main(board_size: int) -> None:
    # ========== 步骤1: 创建约束编程模型 ==========
    # CpModel() 是约束编程模型，用于定义变量和约束
    model = cp_model.CpModel()

    # ========== 步骤2: 创建变量 ==========
    # 创建 board_size 个变量，每个变量代表一列中皇后的行位置
    #
    # 例如：board_size = 8 时
    # queens[0] 表示第 0 列皇后的行位置（范围 0-7）
    # queens[1] 表示第 1 列皇后的行位置（范围 0-7）
    # ...
    # queens[7] 表示第 7 列皇后的行位置（范围 0-7）
    #
    # 使用列表推导式创建变量列表：
    # [表达式 for 变量 in 可迭代对象]
    queens = [model.new_int_var(0, board_size - 1, f"x_{i}") for i in range(board_size)]

    # ========== 步骤3: 添加约束 ==========
    # 约束1: 所有皇后必须在不同行
    # 因为我们每列只放一个皇后，所以只需要确保所有行号不同
    model.add_all_different(queens)

    # 约束2: 没有两个皇后在同一条对角线上
    #
    # 对角线有两种：
    # 1. 主对角线方向（左上到右下）：行号 - 列号 = 常数
    #    例如：(0,0), (1,1), (2,2) 都在一条对角线上，因为 0-0=1-1=2-2=0
    #    所以 queens[i] - i 必须都不同
    #
    # 2. 副对角线方向（右上到左下）：行号 + 列号 = 常数
    #    例如：(0,7), (1,6), (2,5) 都在一条对角线上，因为 0+7=1+6=2+5=7
    #    所以 queens[i] + i 必须都不同
    #
    # 使用生成器表达式：(queens[i] + i for i in range(board_size))
    # 这相当于创建一个临时列表，但不占用内存
    model.add_all_different(queens[i] + i for i in range(board_size))
    model.add_all_different(queens[i] - i for i in range(board_size))

    # ========== 步骤4: 创建求解器并求解 ==========
    # 创建一个 CP-SAT 求解器实例
    solver = cp_model.CpSolver()

    # 创建一个解决方案打印器对象，传入皇后变量列表
    solution_printer = NQueenSolutionPrinter(queens)

    # 设置求解器参数：枚举所有解（而不只是找到一个解就停止）
    solver.parameters.enumerate_all_solutions = True

    # 开始求解模型，传入 solution_printer 作为回调函数
    # 每找到一个解，就会调用 solution_printer.on_solution_callback()
    solver.solve(model, solution_printer)

    # ========== 步骤5: 打印统计信息 ==========
    print("\nStatistics")  # 打印标题 "统计信息"
    # 打印冲突次数（求解器在搜索过程中遇到的约束冲突次数）
    print(f"  conflicts      : {solver.num_conflicts}")
    # 打印分支次数（求解器搜索决策树时的分支数量）
    print(f"  branches       : {solver.num_branches}")
    # 打印求解耗时（单位：秒）
    print(f"  wall time      : {solver.wall_time} s")
    # 打印找到的解的总数
    print(f"  solutions found: {solution_printer.solution_count}")


# Python 的特殊写法
# 如果这个文件被直接运行（而不是被其他文件导入），则执行下面的代码
# __name__ 是 Python 的内置变量，直接运行时值为 "__main__"
if __name__ == "__main__":
    # 默认求解 8×8 的八皇后问题
    size = 8  # 标准的八皇后问题
    # 如果用户在命令行提供了参数，使用用户指定的棋盘大小
    # 例如：python n-queens.py 10  # 求解 10×10 的十皇后问题
    # sys.argv 是命令行参数列表，sys.argv[0] 是脚本名，sys.argv[1] 是第一个参数
    if len(sys.argv) > 1:
        size = int(sys.argv[1])  # 将字符串参数转换为整数
    main(size)  # 调用主函数
