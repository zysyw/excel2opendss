import opendssdirect as dss
from flask import Blueprint, jsonify, render_template
import json
import re

run_opendss_bp = Blueprint('run_opendss_bp', __name__)

transformer_losses = {}
line_losses = {}

def run_opendss(opendss_script_filename):
    global transformer_losses, line_losses
    # 初始化 OpenDSS
    dss.Basic.Start(0)
     
    dss.run_command(f"Redirect [{opendss_script_filename}]")

    # 初始化 OpenDSS
    transformer_losses = {}
    line_losses = {}
    dss.Solution.Number(1)
    for _ in range(24):
        dss.Solution.Solve()
        # 累加每个小时的元件损耗
        # 过滤以 "Sub" 开头或以 "publictransformer" 结尾的变压器，即公用变压器
        pattern = r"^(sub)|(.*publictransformer)$"
        transformer_losses = add_transformer_losses(transformer_losses, get_transformer_losses(filter_pattern=pattern))
        line_losses = add_line_losses(line_losses, get_line_losses())
    
    return {"Load Flow Completed": "Yes" if dss.Solution.Converged() else "No"}

@run_opendss_bp.route('/bus-voltages')
def get_opendss_voltages():
    
    voltages = dss.Circuit.AllBusMagPu()
    
    return jsonify(voltages)

@run_opendss_bp.route('/line-currents')
def get_line_currents():
    line_names = dss.Lines.AllNames()
    currents_data = {}

    for name in line_names:
        dss.Lines.Name(name)
        currents = dss.CktElement.CurrentsMagAng()
        currents_data[name] = currents

    return jsonify(currents_data)

@run_opendss_bp.route('/show_first-meter')
def get_opendss_meters():
    meter_names = dss.Meters.RegisterNames()
    meter_values = dss.Meters.RegisterValues()
    registers = zip(meter_names, meter_values)
    
    return render_template('show_meter_registers.html', registers=registers,)

@run_opendss_bp.route('/circut-losses')
def get_circut_losses():
    global transformer_losses, line_losses
    # 收集 EnergyMeter 数据
    dss.Meters.First()
    meter_data = {}
    json_data = 'Null'
    while True:
        name = dss.Meters.Name()
        registers = dss.Meters.RegisterNames()
        values = dss.Meters.RegisterValues()
        meter_data[name] = dict(zip(registers, values))
        if not dss.Meters.Next() > 0:
            break

    # 整合所有数据并转换为 JSON
    all_data = {
        "EnergyMeters": meter_data,
        "TransformerLosses": transformer_losses,
        "LineLosses": line_losses
    }
    json_data = json.dumps(all_data)

    # 输出 JSON 数据或进行后续处理
    return jsonify(json_data)

def get_transformer_losses(filter_pattern=""):
    # 收集变压器损耗数据
    dss.Transformers.First()
    transformer_losses = {}
    while True:
        name = dss.Transformers.Name()
        print(name[-1])
        # 使用复杂的过滤规则
        if not filter_name(name, filter_pattern):
            losses = {
                "TotalLoss": dss.Transformers.LossesByType()[0]/1000,  # 总损耗,改变单位kVA
                "LoadLoss": dss.Transformers.LossesByType()[2]/1000,  # 负载损耗
                "NoLoadLoss": dss.Transformers.LossesByType()[4]/1000  # 空载损耗
            }
            transformer_losses[name] = losses

        if not dss.Transformers.Next() > 0:
            break

    return transformer_losses

def add_transformer_losses(losses1, losses2):
    # 如果losses1为空，直接返回losses2
    if not losses1:
        return losses2

    sum_losses = {}
    for key in losses1:
        # 确保losses2也包含相同的键
        if key in losses2:
            sum_losses[key] = {
                "TotalLoss": losses1[key]["TotalLoss"] + losses2[key]["TotalLoss"],
                "LoadLoss": losses1[key]["LoadLoss"] + losses2[key]["LoadLoss"],
                "NoLoadLoss": losses1[key]["NoLoadLoss"] + losses2[key]["NoLoadLoss"]
            }
        else:
            # 如果losses2中没有对应的键，只使用losses1的值
            sum_losses[key] = losses1[key]
    
    return sum_losses

def get_line_losses():
    # 收集线路损耗数据
    dss.Lines.First()
    line_losses = {}
    while True:
        name = dss.Lines.Name()
        # 获取损耗（返回的是一个包含有功和无功损耗的元组）
        losses = dss.CktElement.Losses()[0]/1000
        line_losses[name] = losses
        if not dss.Lines.Next() > 0:
            break
    return line_losses

def add_line_losses(losses1, losses2):
    # 如果losses1为空，直接返回losses2
    if not losses1:
        return losses2

    sum_losses = {}
    for key in losses1:
        # 确保losses2也包含相同的键
        if key in losses2:
            sum_losses[key] = losses1[key] + losses2[key]
        else:
            # 如果losses2中没有对应的键，只使用losses1的值
            sum_losses[key] = losses1[key]

    return sum_losses

def filter_name(name, pattern):
    """
    根据提供的模式过滤名称。
    返回 True 如果名称与模式匹配，否则返回 False。
    """
    return re.match(pattern, name) is not None