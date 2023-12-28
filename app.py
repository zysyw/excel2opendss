from flask import Flask, request, jsonify, render_template_string
import opendssdirect as dss

app = Flask(__name__)

# 使用一个全局变量来存储接收到的数据
received_data = None

@app.route('/')
def hello():
    return 'Hello, World!'

@app.route('/process-data', methods=['GET', 'POST'])
def process_data():
    global received_data
    if request.method == 'POST':
        # 解析接收的 JSON 数据
        data = request.json
        
        # 接收并存储 JSON 数据，以便显示接收到的数据
        received_data = data

        # 调用函数来处理数据并生成 OpenDSS 脚本
        dss_script_filename = generate_dss_script(data)

        # 运行 OpenDSS 计算
        result = run_opendss(dss_script_filename)

        return jsonify(result)
    else:
        # GET 请求，显示接收到的数据
        return render_template_string("""
            <!doctype html>
            <html>
            <body>
                <h1>Received JSON Data:</h1>
                <pre>{{ data }}</pre>
            </body>
            </html>
        """, data=received_data)

def generate_dss_script(data):
    # 处理 JSON 数据并生成 OpenDSS 脚本
    # 使用 Jinja2 或其他方法
    

    # 确保 JSON 数据的第一层只有一个键值对
    if len(data) != 1:
        raise ValueError("JSON 数据应该只包含一个顶级键")

    # 获取顶级键名
    top_level_key = list(data.keys())[0]
    top_level_data = data[top_level_key]
    
    script_filename = f"{top_level_key}.dss"

    from jinja2 import Environment, FileSystemLoader
    # 设置 Jinja2 环境
    env = Environment(
        loader=FileSystemLoader('.'),
        trim_blocks=True,
        lstrip_blocks=True
    )
    template = env.get_template('opendss_template.j2')
    opendss_script = template.render(top_level_key=top_level_key, top_level_data=top_level_data)
    
    with open(script_filename, "w") as file:
        file.write(opendss_script)
                    
    #print(opendss_script)
    return script_filename

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
