"""
车间作业调度问题（Job Shop Scheduling）最小示例

问题简介：
车间作业调度是一个经典的优化问题。在一个车间中，有多台机器，每个作业由多个工序组成，
每个工序必须在指定的机器上加工，且每个作业的工序有固定的顺序约束。
目标是如何安排所有工序的加工顺序，使得总的完工时间（makespan）最短。

示例说明：
本示例使用 Google OR-Tools 的约束规划求解器（CP-SAT）来解决这个问题。
"""
import collections
from ortools.sat.python import cp_model


def main() -> None:
    """车间作业调度问题主函数"""
    # ==================== 数据定义 ====================
    # jobs_data 定义了所有作业及其工序
    # 格式: 每个作业是一个列表，包含多个工序
    # 每个工序是一个元组 (machine_id, processing_time)
    # machine_id: 使用的机器编号
    # processing_time: 在该机器上的加工时间
    jobs_data = [
        [(0, 3), (1, 2), (2, 2)],  # 作业0: 先在机器0加工3小时，再在机器1加工2小时，最后在机器2加工2小时
        [(0, 2), (2, 1), (1, 4)],  # 作业1: 先在机器0加工2小时，再在机器2加工1小时，最后在机器1加工4小时
        [(1, 4), (2, 3)],          # 作业2: 先在机器1加工4小时，再在机器2加工3小时
    ]

    # 计算机器总数：找到所有工序中最大的机器编号，然后加1（因为机器编号从0开始）
    # 例如：如果最大机器编号是2，那么机器总数就是3台（机器0、1、2）
    machines_count = 1 + max(task[0] for job in jobs_data for task in job)
    all_machines = range(machines_count)

    # 计算时间范围（horizon）：所有工序加工时间的总和
    # 这是整个调度可能的最长完成时间，用作变量上界
    horizon = sum(task[1] for job in jobs_data for task in job)

    # ==================== 创建约束规划模型 ====================
    model = cp_model.CpModel()

    # ==================== 定义数据结构 ====================
    # 使用命名元组（namedtuple）存储任务变量信息
    # start: 工序开始时间变量
    # end: 工序结束时间变量
    # interval: 时间间隔变量（包含开始时间、持续时间、结束时间）
    task_type = collections.namedtuple("task_type", "start end interval")

    # 使用命名元组存储已分配的任务信息（用于输出结果）
    # start: 实际开始时间
    # job: 作业编号
    # index: 工序编号
    # duration: 加工时间
    assigned_task_type = collections.namedtuple(
        "assigned_task_type", "start job index duration"
    )

    # ==================== 创建变量 ====================
    # all_tasks: 存储所有工序的变量，键为 (job_id, task_id) 元组
    # machine_to_intervals: 存储每台机器上的所有时间间隔（工序）
    all_tasks = {}
    machine_to_intervals = collections.defaultdict(list)

    # 遍历所有作业和工序，为每个工序创建变量
    for job_id, job in enumerate(jobs_data):
        for task_id, task in enumerate(job):
            machine, duration = task  # machine: 使用的机器，duration: 加工时长

            # 创建后缀用于变量命名，例如 "_0_1" 表示作业0的工序1
            suffix = f"_{job_id}_{task_id}"

            # 创建整数变量：工序的开始时间，范围从0到horizon
            start_var = model.new_int_var(0, horizon, "start" + suffix)

            # 创建整数变量：工序的结束时间，范围从0到horizon
            end_var = model.new_int_var(0, horizon, "end" + suffix)

            # 创建间隔变量：表示一个时间段（开始时间，持续时间，结束时间）
            interval_var = model.new_interval_var(
                start_var, duration, end_var, "interval" + suffix
            )

            # 将变量存储到字典中，方便后续访问
            all_tasks[job_id, task_id] = task_type(
                start=start_var, end=end_var, interval=interval_var
            )

            # 将该工序的时间间隔添加到对应机器的列表中
            machine_to_intervals[machine].append(interval_var)

    # ==================== 添加约束条件 ====================
    # 约束1：同一台机器上同一时间只能加工一个工序（互斥约束）
    # 这确保了机器上的工序不会重叠
    for machine in all_machines:
        model.add_no_overlap(machine_to_intervals[machine])

    # 约束2：同一个作业内的工序必须按顺序执行（优先级约束）
    # 确保工序 task_id+1 必须在工序 task_id 完成后才能开始
    for job_id, job in enumerate(jobs_data):
        for task_id in range(len(job) - 1):
            model.add(
                all_tasks[job_id, task_id + 1].start >= all_tasks[job_id, task_id].end
            )

    # ==================== 设置目标函数 ====================
    # 目标：最小化总完工时间（makespan）
    # makespan 是所有作业中最后一个工序的完成时间

    # 创建一个变量来表示 makespan
    obj_var = model.new_int_var(0, horizon, "makespan")

    # 将 obj_var 设置为所有作业最后一道工序结束时间的最大值
    model.add_max_equality(
        obj_var,
        [all_tasks[job_id, len(job) - 1].end for job_id, job in enumerate(jobs_data)],
    )

    # 设置优化目标：最小化 makespan
    model.minimize(obj_var)

    # ==================== 求解 ====================
    # 创建求解器实例
    solver = cp_model.CpSolver()

    # 调用求解器求解模型
    status = solver.solve(model)

    # ==================== 输出结果 ====================
    # 检查求解状态：找到最优解或可行解
    if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
        print("Solution:")

        # 按机器整理已分配的任务
        # assigned_jobs 是一个字典，键是机器编号，值是该机器上的任务列表
        assigned_jobs = collections.defaultdict(list)
        for job_id, job in enumerate(jobs_data):
            for task_id, task in enumerate(job):
                machine = task[0]  # 获取该工序使用的机器
                assigned_jobs[machine].append(
                    assigned_task_type(
                        start=solver.value(all_tasks[job_id, task_id].start),  # 获取变量的实际值
                        job=job_id,
                        index=task_id,
                        duration=task[1],
                    )
                )

        # 构建输出字符串
        output = ""
        for machine in all_machines:
            # 按开始时间排序（默认按命名元组的第一个字段排序）
            assigned_jobs[machine].sort()

            # 第一行：显示任务名称
            sol_line_tasks = "Machine " + str(machine) + ": "
            # 第二行：显示时间区间
            sol_line = "           "

            for assigned_task in assigned_jobs[machine]:
                # 生成任务名称，如 "job_0_task_1"
                name = f"job_{assigned_task.job}_task_{assigned_task.index}"
                # 添加到输出行，:15 表示占15个字符宽度，右对齐
                sol_line_tasks += f"{name:15}"

                # 计算时间区间，如 "[0,3]" 表示从时间0开始，到时间3结束
                start = assigned_task.start
                duration = assigned_task.duration
                sol_tmp = f"[{start},{start + duration}]"
                # 添加到输出行，:15 表示占15个字符宽度，右对齐
                sol_line += f"{sol_tmp:15}"

            # 添加换行符
            sol_line += "\n"
            sol_line_tasks += "\n"
            output += sol_line_tasks
            output += sol_line

        # 打印最优解的调度长度和完整调度方案
        print(f"Optimal Schedule Length: {solver.objective_value}")
        print(output)
    else:
        # 没有找到可行解
        print("No solution found.")

    # ==================== 输出统计信息 ====================
    print("\nStatistics")
    print(f"  - conflicts: {solver.num_conflicts}")  # 冲突次数
    print(f"  - branches : {solver.num_branches}")   # 分支次数
    print(f"  - wall time: {solver.wall_time}s")     # 实际运行时间


if __name__ == "__main__":
    main()