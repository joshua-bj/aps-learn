# 导入 io 模块，用于处理字符串输入输出
# io.StringIO 可以将字符串当作文件来处理
import io

# 导入 pandas 库，用于数据处理和分析
# pd 是 pandas 的常用别名
import pandas as pd

# 从 ortools 库导入约束编程（CP）模块
from ortools.sat.python import cp_model


def main() -> None:
    # ========== 步骤1: 准备数据 ==========
    # 使用三引号字符串定义多行文本数据
    # 这是一个包含工人、任务和成本的表格
    # 每行表示：某个工人完成某个任务的成本
    data_str = """
  worker  task  cost
      w1    t1    90
      w1    t2    80
      w1    t3    75
      w1    t4    70
      w2    t1    35
      w2    t2    85
      w2    t3    55
      w2    t4    65
      w3    t1   125
      w3    t2    95
      w3    t3    90
      w3    t4    95
      w4    t1    45
      w4    t2   110
      w4    t3    95
      w4    t4   115
      w5    t1    50
      w5    t2   110
      w5    t3    90
      w5    t4   100
  """

    # 使用 pandas 读取数据
    # io.StringIO(data_str) 将字符串转换为类似文件的对象
    # sep=r"\s+" 表示使用一个或多个空白字符作为分隔符（正则表达式）
    # 这样可以处理不规则的空格
    data = pd.read_table(io.StringIO(data_str), sep=r"\s+")

    # 打印加载的数据，方便查看
    print("=" * 60)
    print("【原始数据】data = pd.read_table(...)")
    print("=" * 60)
    print(data)
    print("\n数据类型：")
    print(data.dtypes)
    print("\n数据形状（行数，列数）：")
    print(f"  {data.shape}")
    print("\n数据索引：")
    print(f"  {data.index.tolist()}")
    print("=" * 60, "\n")

    # ========== 步骤2: 创建约束编程模型 ==========
    # CpModel() 是约束编程模型，用于定义变量和约束
    model = cp_model.CpModel()

    # ========== 步骤3: 创建变量 ==========
    # 创建布尔变量序列
    # x 是一个布尔变量列表，每个变量代表一个可能的分配
    # x[i] = True 表示选择第 i 行的工人-任务分配
    # x[i] = False 表示不选择第 i 行的工人-任务分配
    # data.index 是 pandas DataFrame 的行索引（0, 1, 2, ..., 19）
    x = model.new_bool_var_series(name="x", index=data.index)

    # ========== 步骤4: 添加约束 ==========
    # 约束1: 每个工人最多分配一个任务
    #
    # data.groupby("worker") 按照工人分组
    # tasks 是同一个工人的所有任务的数据
    # unused_name 是工人的名称（我们用不上，所以叫 unused_name）
    for unused_name, tasks in data.groupby("worker"):
        # add_at_most_one() 表示最多只能选择一个 True
        # x[tasks.index] 是这个工人对应的任务变量列表
        model.add_at_most_one(x[tasks.index])

    # 约束2: 每个任务必须分配给恰好一个工人
    #
    # data.groupby("task") 按照任务分组
    # workers 是同一个任务的所有工人的数据
    for unused_name, workers in data.groupby("task"):
        # add_exactly_one() 表示必须恰好选择一个 True
        # x[workers.index] 是这个任务对应的工人变量列表
        model.add_exactly_one(x[workers.index])

    # ========== 步骤5: 设置目标函数 ==========
    # 最小化总成本
    # data.cost.dot(x) 计算成本和布尔变量的点积
    # 相当于：sum(cost[i] * x[i] for i in range(len(cost)))
    # 因为 x 是布尔变量，只有被选中的分配（x[i]=1）才会计算成本
    model.minimize(data.cost.dot(x))

    # ========== 步骤6: 求解模型 ==========
    # 创建一个 CP-SAT 求解器实例
    solver = cp_model.CpSolver()

    # 求解模型，返回求解状态
    # status 可能的值：OPTIMAL（最优解）, FEASIBLE（可行解）, INFEASIBLE（无解）等
    status = solver.solve(model)

    # ========== 步骤7: 打印解 ==========
    # 检查求解状态
    # cp_model.OPTIMAL: 找到了最优解
    # cp_model.FEASIBLE: 找到了可行解（但不一定是最优的）
    if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
        # 打印总成本（目标函数的值）
        print(f"Total cost = {solver.objective_value}\n")

        # 获取被选中的分配
        # solver.boolean_values(x) 返回所有布尔变量的值
        # .loc[lambda x: x] 是一个过滤操作，只保留值为 True 的行
        selected = data.loc[solver.boolean_values(x).loc[lambda x: x].index]

        # 遍历所有被选中的分配
        # unused_index 是行索引（用不上）
        # row 是该行的数据（包含 worker, task, cost）
        for unused_index, row in selected.iterrows():
            # 打印每个分配的结果
            print(f"{row.task} assigned to {row.worker} with a cost of {row.cost}")

    # 如果没有找到可行解
    elif status == cp_model.INFEASIBLE:
        print("No solution found")

    # 其他情况（异常情况）
    else:
        print("Something is wrong, check the status and the log of the solve")


# Python 的特殊写法
# 如果这个文件被直接运行（而不是被其他文件导入），则执行下面的代码
# __name__ 是 Python 的内置变量，直接运行时值为 "__main__"
if __name__ == "__main__":
    main()
