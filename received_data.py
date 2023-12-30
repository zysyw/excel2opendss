from flask import Blueprint, current_app, render_template
import json

# 创建一个蓝图
received_data_bp = Blueprint('received_data_bp', __name__)

@received_data_bp.route('/received-data')
def receive_data():
    data = current_app.config['received_data']
    data_str = json.dumps(data, ensure_ascii=False)
    #print(data_str)
    return render_template('show_data.html', dict_data=data_str)