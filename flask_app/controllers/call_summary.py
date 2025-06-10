from flask_app import app
from flask import render_template, redirect, request, session, flash, url_for, send_file
import pandas as pd
import os
import time
import zipfile
from werkzeug.utils import secure_filename

def allowed_file(filename):
    return '.' in filename and \
            filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

def zip_single_file(file_path, zip_path):
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        return None

    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        arcname = os.path.basename(file_path)
        zipf.write(file_path, arcname=arcname)
        print(f"Added {arcname} to zip")

    return zip_path

def csv_to_excel(file_path):
    base_dir = os.path.abspath(os.path.dirname(__file__))
    reports_folder = os.path.join(base_dir, '..', 'reports')
    os.makedirs(reports_folder, exist_ok=True)

    df = pd.read_csv(file_path)

    timestamp = time.strftime("%Y-%m-%d_%H-%M-%S")

    avg_duration_call_type = df.groupby('reason')['call_duration_seconds'].agg(['count', 'mean'])

    top_reason = avg_duration_call_type['mean'].idxmax()
    top_avg_duration = avg_duration_call_type['mean'].max()

    reason_summary = avg_duration_call_type.reset_index()

    reason_summary.columns = ['Reason for Call', 'Number of Calls', 'Mean Call Time Seconds']
    reason_summary = reason_summary.sort_values(by='Number of Calls', ascending=False)
    reason_summary = reason_summary.reset_index(drop=True)


    most_common_reason  = reason_summary.iloc[0]['Reason for Call']
    most_common_reason_count = reason_summary.iloc[0]['Number of Calls']
    print(reason_summary)
    print(f"The most common call reason was {most_common_reason} having {most_common_reason_count} calls, and the call reason with the greatest call duration is '{top_reason}' with the average duration being {top_avg_duration} seconds.")

    excel_filename = f"call_summary_report_{timestamp}.xlsx"
    excel_path = os.path.join(reports_folder, excel_filename) 

    try:
        reason_summary.to_excel(excel_path, index=False)
        print(f"Excel file {excel_path} successfully created")
    except Exception as e:
        print(f"Failed to create {excel_path} in excel: {e}")

    zip_filename = f'report_{timestamp}.zip'
    zip_path = os.path.join(reports_folder, zip_filename)

    zip_single_file(excel_path, zip_path)
    os.remove(excel_path)

    session['zip_report_filename'] = zip_filename

    return

# @app.route('/', methods=['GET', 'POST'])
# def root():
#     if request.method == 'POST':
#         file = request.files.get('file')
#         if not file or file.filename == '':
#             flash('No file uploaded.', 'File')
#             return render_template('index.html')

#         if file and allowed_file(file.filename):
#             filename = secure_filename(file.filename)
#             filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
#             file.save(filepath)
#             print('successful file save')

#             csv_to_excel(filepath)

#             return render_template('index.html', report_ready=True, filename=session['zip_report_filename'])

#         flash('Invalid file type*', 'File')
#         return render_template('index.html')

#     return render_template('index.html')

@app.route('/')
def root():
    return render_template('index.html')

@app.route('/download_template')
def template_download():
    base_dir = os.path.abspath(os.path.dirname(__file__))
    template_csv = os.path.join(base_dir, '..', 'sample_template', 'calls.csv')
    zip_file = os.path.join(base_dir, '..', 'sample_template', 'template_download.zip')

    zip_single_file(template_csv, zip_file)

    return send_file(zip_file, as_attachment=True)


@app.route('/upload', methods=['POST'])
def upload_file():
    file = request.files['file']
    if file.filename == '':
        flash('No file selected*', 'File')
        return redirect('/')
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        print('successful file save')

        csv_to_excel(filepath) 

        return redirect('/report-ready')
    flash('Invalid file type*', 'File')
    return redirect('/')

@app.route('/report-ready')
def report_ready():
    filename = session.get('zip_report_filename')
    print(filename)
    if not filename:
        flash('You must upload a file before viewing the report.', 'File')
        return redirect(url_for('root'))
    
    session.clear()

    return render_template('report_ready.html', filename=filename)

@app.route('/download/<filename>')
def download_report(filename):
    base_dir = os.path.abspath(os.path.dirname(__file__))
    zip_path = os.path.join(base_dir, '..', 'reports', filename)

    if os.path.exists(zip_path):
        return send_file(zip_path, as_attachment=True)

    flash('File not found*', 'File')
    return redirect(url_for('root'))