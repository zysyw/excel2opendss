import os
from flask import Flask, request, jsonify
from opendss_script.generate_dss_script import generate_dss_script
from opendss_calculation.run_opendss import run_opendss
from received_data import received_data_bp
from opendss_script.generate_dss_script import opendss_script_bp
from opendss_calculation.run_opendss import run_opendss_bp

app = Flask(__name__)

# 使用config来保存需要显示的内容
app.config['received_data'] = None
app.config['opendss_script_file'] = None

# 显示json数据、opendss脚本文件、opendss计算结果的蓝图
app.register_blueprint(received_data_bp)
app.register_blueprint(opendss_script_bp)
app.register_blueprint(run_opendss_bp)

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

if __name__ == "__main__":
    app.run(debug=True)
