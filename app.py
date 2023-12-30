import os
from flask import Flask, request, jsonify
from opendss_script.generate_dss_script import generate_dss_script
from received_data import received_data_bp
from opendss_script.generate_dss_script import opendss_script_bp
import opendssdirect as dss

app = Flask(__name__)

# 使用config来保存需要显示的内容
app.config['received_data'] = None
app.config['opendss_script_file'] = None

# 显示json数据、opendss脚本文件、opendss计算结果的蓝图
app.register_blueprint(received_data_bp)
app.register_blueprint(opendss_script_bp)

# 初始化 OpenDSS
#dss.Basic.Start(0)
#app.config['dss'] = dss  # 将 OpenDSS 实例存储在 app.config 中

@app.route('/')
def index():
    return '这是一个线损计算服务，前端利用Excel输入格式化数据，后端利用jinja2模板将json数据转换成opendss脚本文件，再利用opendssdirect.py进行计算。'

@app.route('/process-data', methods=['POST'])
def process_data():
    
    # 接收 JSON 数据
    data = request.json
    app.config['received_data'] = data

    # 生成 OpenDSS 脚本文件, 生成的脚本文件放在工程路径下的opendss_script_files中
    dss_script_filename = generate_dss_script(data, os.path.join("opendss_script_files"))
    app.config['opendss_script_file'] = dss_script_filename

    # 运行 OpenDSS 计算
    result = run_opendss(dss_script_filename)

    return jsonify(result)

def run_opendss(opendss_script_filename):

    # 初始化 OpenDSS
    dss.Basic.Start(0)
     
    dss.run_command(f"Redirect [{opendss_script_filename}]")

    dss.Solution.Solve()
    
    return {"Load Flow Completed": "Yes" if dss.Solution.Converged() else "No"}

@app.route('/get-voltages')
def get_opendss_voltages():
    
    #print("Load Flow Completed:", "Yes" if dss.Solution.Converged() else "No")
    voltages = dss.Circuit.AllBusMagPu()
    #print("Bus Voltages (pu):", voltages)
    
    return jsonify(voltages)

@app.route('/get-line-currents')
def get_line_currents():
    line_names = dss.Lines.AllNames()
    currents_data = {}

    for name in line_names:
        dss.Lines.Name(name)
        currents = dss.CktElement.CurrentsMagAng()
        currents_data[name] = currents

    return jsonify(currents_data)


@app.route('/get-meters')
def get_opendss_meters():
    
    #print("Load Flow Completed:", "Yes" if dss.Solution.Converged() else "No")
    meter_values = dss.Meters.RegisterValues()
    print("Meter Values:", meter_values)
    
    return jsonify(meter_values)

if __name__ == "__main__":
    app.run(debug=True)
