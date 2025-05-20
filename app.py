from flask import Flask, render_template, request, redirect, flash, url_for
import pandas as pd
import csv
import folium
from folium import Popup
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = '미소는짱123' 

UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.template_filter('facility_name')
def facility_name(key):
    names = {
        'ramp': '경사로',
        'toilet': '장애인 화장실',
        'elevator': '장애인 엘리베이터',
        'handrail': '핸드레일'
    }
    return names.get(key, key)


# CSV 데이터 로드
def load_data():
    return pd.read_csv('facilities.csv')

def generate_map(data):
    m = folium.Map(location=[37.5880, 126.9935], zoom_start=17)

    for _, row in data.iterrows():
        facilities = []
        if row['ramp']: facilities.append('경사로')
        if row['toilet']: facilities.append('장애인 화장실')
        if row['elevator']: facilities.append('장애인 엘리베이터')
        if row['handrail']: facilities.append('핸드레일')

        # 말풍선 내용 (줄바꿈 포함된 HTML)
        popup_html = f"""
        <b>{row['building_name']}</b><br>
        {', '.join(facilities)}
        """

        folium.Marker(
            location=[row['lat'], row['lng']],
            popup=Popup(popup_html, max_width=300),
            icon=folium.Icon(color='blue', icon='info-sign')
        ).add_to(m)

    m.save('templates/map.html')

@app.route('/')
def index():
    data = load_data()
    selected_building = request.args.get('building')
    selected_filters = {
        'ramp': request.args.get('ramp'),
        'toilet': request.args.get('toilet'),
        'elevator': request.args.get('elevator'),
        'handrail': request.args.get('handrail'),
    }

    result = None
    if selected_building:
        building_data = data[data['building_name'] == selected_building]
        if not building_data.empty:
            building_info = building_data.iloc[0]
            result = {
                'building': selected_building,
                'results': {}
            }
            for key, checked in selected_filters.items():
                if checked is not None:
                    result['results'][key] = bool(building_info[key])
    return render_template('index.html', facilities=data.to_dict(orient='records'), result=result)

@app.route('/map')
def map_view():
    data = pd.read_csv('facilities.csv')
    generate_map(data)
    return render_template('map.html')

@app.route('/report', methods=['GET', 'POST'])
def report():
    data = load_data()

    if request.method == 'POST':
        building = request.form['building']
        detail = request.form['detail']  # ✅ 이제 입력값은 이거 하나!
        photo = request.files['photo']
        filename = ""

        # 파일이 있다면 저장
        if photo and allowed_file(photo.filename):
            filename = secure_filename(photo.filename)
            upload_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            if not os.path.exists(app.config['UPLOAD_FOLDER']):
                os.makedirs(app.config['UPLOAD_FOLDER'])
            photo.save(upload_path)

        # CSV 저장: 이제 'issue' 없이 building, detail, photo_filename만 저장
        with open('feedback.csv', 'a', newline='', encoding='utf-8-sig') as f:
            writer = csv.writer(f)
            writer.writerow([building, detail, filename])

        flash('제보가 성공적으로 제출되었습니다!')
        return redirect(url_for('report'))

    return render_template('report.html', facilities=data.to_dict(orient='records'))


if __name__ == '__main__':
    app.run()

