from flask import Blueprint, render_template, current_app
import os

opendss_script_bp = Blueprint('opendss_script_bp', __name__)

@opendss_script_bp.route('/opendss-script')
def show_opendss_script():
    # 从配置中获取文件名
    script_file = current_app.config.get('opendss_script_file', '')
    print("Script file from config:", script_file)

    # 检查文件名是否存在且文件是否可读
    if script_file and os.path.isfile(script_file):
        with open(script_file, 'r') as file:
            content = file.readlines()
    else:
        content = ["未生成OpenDSS脚本文件"]

    # 返回渲染的模板
    return render_template('show_script.html', filename=script_file, content=content)

def generate_dss_script(data, script_filepath):
    # 使用 Jinja2 生成 OpenDSS 脚本

    # 确保 JSON 数据的第一层只有一个键值对：excel侧形成json的规则是以文件名为key，所有的数据打包成value
    if len(data) != 1:
        raise ValueError("JSON 数据应该只包含一个顶级键")

    # 获取顶级键名，也即文件名
    top_level_key = list(data.keys())[0]
    top_level_data = data[top_level_key]
    
    script_filename =  os.path.join(script_filepath, f"{top_level_key}.dss")

    from jinja2 import Environment, FileSystemLoader
    # 设置 Jinja2 环境
    env = Environment(
        loader=FileSystemLoader(os.path.dirname(os.path.abspath(__file__))),
        trim_blocks=True,
        lstrip_blocks=True
    )
    template = env.get_template('opendss_template.j2')
    opendss_script = template.render(top_level_key=top_level_key, top_level_data=top_level_data)
    
    with open(script_filename, "w") as file:
        file.write(opendss_script)
                    
    #print(opendss_script)
    return script_filename