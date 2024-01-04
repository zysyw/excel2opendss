import opendssdirect as dss
from flask import Blueprint, jsonify, render_template
import json

run_opendss_bp = Blueprint('run_opendss_bp', __name__)

def run_opendss(opendss_script_filename):

    # 初始化 OpenDSS
    dss.Basic.Start(0)
     
    dss.run_command(f"Redirect [{opendss_script_filename}]")

    dss.Solution.Solve()
    
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
    dss.Solution.Number(1)
    dss.Solution.Solve()
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

    # 收集变压器损耗数据
    dss.Transformers.First()
    transformer_losses = {}
    while True:
        name = dss.Transformers.Name()
        print(name)
        print(dss.Transformers.LossesByType())
        losses = {
            "TotalLoss": dss.Transformers.LossesByType()[0]/1000,  # 总损耗,改变单位kVA
            "LoadLoss": dss.Transformers.LossesByType()[2]/1000,  # 负载损耗
            "NoLoadLoss": dss.Transformers.LossesByType()[4]/1000  # 空载损耗
        }
        transformer_losses[name] = losses
        if not dss.Transformers.Next() > 0:
            break

    # 收集线路损耗数据
    dss.Lines.First()
    line_losses = {}
    while True:
        name = dss.Lines.Name()
        # 获取损耗（返回的是一个包含有功和无功损耗的元组）
        losses = dss.CktElement.Losses()[0].real
        line_losses[name] = losses
        if not dss.Lines.Next() > 0:
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