# 从 Google OR-Tools 库导入约束规划（CP）模型模块
# OR-Tools 是 Google 开源的开源运筹学优化工具套件
from ortools.sat.python import cp_model


def main():
    # 创建一个约束规划模型实例
    # CpModel 用于定义变量、约束和目标函数
    model = cp_model.CpModel()

    # ----------------------------
    # 数据定义
    # ----------------------------
    # 定义三个作业（Job）的数据
    # 每个作业是一个列表，包含多个任务
    # 每个任务是一个元组：(机器编号, 持续时间)
    jobs_data = [
        [(0, 2), (1, 3)],  # 作业 A：在机器0上加工2小时，然后在机器1上加工3小时
        [(0, 4), (1, 2)],  # 作业 B：在机器0上加工4小时，然后在机器1上加工2小时
        [(0, 3), (1, 3)],  # 作业 C：在机器0上加工3小时，然后在机器1上加工3小时
    ]

    # 机器总数
    machines_count = 2
    # 计算时间上界（horizon）：所有任务时长的总和
    # 这是一个生成器表达式，遍历所有作业的所有任务，累加每个任务的时长
    # 这是最坏情况下所有任务串行执行的总时间
    horizon = sum(task[1] for job in jobs_data for task in job)

    # ----------------------------
    # 变量定义
    # ----------------------------
    # 创建一个字典，用于存储所有任务的变量
    # 键是 (作业ID, 任务ID) 元组，值是 (开始时间, 结束时间, 时间间隔变量)
    all_tasks = {}
    # 创建一个字典，为每台机器初始化一个空列表
    # 用于存储在该机器上执行的所有任务的时间间隔
    # 使用字典推导式：{key: value for item in iterable}
    machine_to_intervals = {i: [] for i in range(machines_count)}

    # 遍历所有作业和任务，创建变量
    # enumerate() 函数返回 (索引, 元素) 对
    for job_id, job in enumerate(jobs_data):  # 遍历每个作业，job_id 是作业编号
        for task_id, (machine, duration) in enumerate(job):  # 遍历作业中的每个任务
            # 创建一个整数变量，表示任务的开始时间
            # 参数：最小值(0), 最大值(horizon), 变量名称
            start_var = model.NewIntVar(0, horizon, f"start_{job_id}_{task_id}")
            # 创建一个整数变量，表示任务的结束时间
            end_var = model.NewIntVar(0, horizon, f"end_{job_id}_{task_id}")
            # 创建一个间隔变量（IntervalVar），表示任务在时间轴上的占用
            # 间隔变量包含：开始时间、持续时间、结束时间
            interval_var = model.NewIntervalVar(
                start_var, duration, end_var,
                f"interval_{job_id}_{task_id}"
            )

            # 将当前任务的变量存储到字典中
            all_tasks[(job_id, task_id)] = (start_var, end_var, interval_var)
            # 将当前任务的间隔变量添加到对应机器的列表中
            machine_to_intervals[machine].append(interval_var)

    # ----------------------------
    # 约束：机器不可重叠
    # ----------------------------
    # 遍历每台机器，添加"无重叠"约束
    # NoOverlap 约束确保同一台机器上的任务在时间上不能重叠
    for machine in range(machines_count):
        model.AddNoOverlap(machine_to_intervals[machine])

    # ----------------------------
    # 约束：工序顺序
    # ----------------------------
    # 确保同一作业内的任务按顺序执行
    # 前一个任务结束后，下一个任务才能开始
    for job_id, job in enumerate(jobs_data):
        # range(len(job) - 1) 生成从 0 到 len(job)-2 的整数
        # 这确保我们不会访问超出索引的任务（task_id + 1）
        for task_id in range(len(job) - 1):
            # 添加约束：当前任务的结束时间 <= 下一个任务的开始时间
            # all_tasks[(job_id, task_id)][1] 获取当前任务的结束时间变量
            # all_tasks[(job_id, task_id + 1)][0] 获取下一个任务的开始时间变量
            model.Add(
                all_tasks[(job_id, task_id)][1] <=
                all_tasks[(job_id, task_id + 1)][0]
            )

    # ----------------------------
    # 目标：最小化最大完工时间
    # ----------------------------
    # 创建一个整数变量表示"完工时间"（makespan）
    # 完工时间是指所有作业中最后一个任务的结束时间
    makespan = model.NewIntVar(0, horizon, "makespan")

    # 创建列表推导式，收集所有作业的最后一个任务的结束时间
    # len(job) - 1 获取每个作业的最后一个任务的索引
    # [1] 获取该任务的结束时间变量（元组的第二个元素）
    last_tasks = [
        all_tasks[(job_id, len(job) - 1)][1]
        for job_id, job in enumerate(jobs_data)
    ]

    # 添加约束：makespan 等于所有最后任务结束时间的最大值
    # AddMaxEquality 将变量设置为等于给定列表的最大值
    model.AddMaxEquality(makespan, last_tasks)
    # 设置优化目标：最小化 makespan
    # 求解器会尝试找到让所有作业尽快完成的最优调度方案
    model.Minimize(makespan)

    # ----------------------------
    # 求解
    # ----------------------------
    # 创建一个约束规划求解器实例
    solver = cp_model.CpSolver()
    # 调用求解器求解模型
    # Solve() 方法返回求解状态：OPTIMAL(最优解)、FEASIBLE(可行解)、INFEASIBLE(无解)等
    status = solver.Solve(model)

    # 检查求解状态
    # cp_model.OPTIMAL 表示找到了最优解
    # cp_model.FEASIBLE 表示找到了可行解（但不一定是最优的）
    if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
        # 打印最优（或可行）的完工时间
        # solver.Value(variable) 获取变量在解中的具体值
        print(f"最优完工时间: {solver.Value(makespan)}\n")
        print(f"解状态: {status}\n")

        # 遍历所有作业和任务，打印每个任务的开始时间
        for job_id, job in enumerate(jobs_data):
            for task_id in range(len(job)):
                # 获取任务的开始时间值
                start = solver.Value(all_tasks[(job_id, task_id)][0])
                # 使用 f-string 格式化输出
                # f"..." 允许在字符串中使用 {变量} 直接插入变量值
                print(
                    f"Job {job_id} Task {task_id} "
                    f"starts at {start}"
                )
    else:
        # 如果没有找到可行解，输出提示信息
        print("无可行解")


# Python 的特殊变量和条件判断
# __name__ 是 Python 的内置变量
# 当直接运行此文件时（如 python sample.py），__name__ 的值是 "__main__"
# 当此文件被其他文件导入时（如 import sample），__name__ 的值是模块名 "sample"
# 这个判断确保：只有在直接运行此文件时才会执行 main() 函数
if __name__ == "__main__":
    main()
