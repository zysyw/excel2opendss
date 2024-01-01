import opendssdirect as dss
from flask import Blueprint, jsonify, render_template

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

@run_opendss_bp.route('/first-meter')
def get_opendss_meters():
    meter_names = dss.Meters.RegisterNames()
    meter_values = dss.Meters.RegisterValues()
    registers = zip(meter_names, meter_values)
    
    return render_template('show_meter_registers.html', registers=registers,)