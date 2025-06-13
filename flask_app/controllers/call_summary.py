from flask_app import app
from flask import render_template, redirect, request, session, flash, url_for, send_file
import pandas as pd
import os
import time
import zipfile
from werkzeug.utils import secure_filename

def get_uploads_folder():
    return app.config['UPLOAD_FOLDER']

def get_reports_folder():
    return app.config['REPORTS_FOLDER']

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
    # reports_folder = os.path.join(base_dir, '..', 'reports')
    os.makedirs(get_reports_folder(), exist_ok=True)

    df = pd.read_csv(file_path)

    summary = df.groupby('reason')['call_duration_seconds'].agg(Calls='count', AvgDuration='mean').reset_index()
    summary = summary.rename(columns={'reason': 'Reason for Call', 'Calls': 'Number of Calls', 'AvgDuration': 'Mean Call Time Seconds'})
    summary = summary.sort_values(by='Number of Calls', ascending=False).reset_index(drop=True)

    timestamp = time.strftime("%Y-%m-%d_%H-%M-%S")
    excel_filename = f"call_summary_report_{timestamp}.xlsx"
    excel_path = os.path.join(get_reports_folder(), excel_filename) 

    try:
        summary.to_excel(excel_path, index=False)
        print(f"Excel file {excel_path} successfully created")
    except Exception as e:
        print(f"Failed to create {excel_path} in excel: {e}")

    zip_filename = f'report_{timestamp}.zip'
    zip_path = os.path.join(get_reports_folder(), zip_filename)

    zip_single_file(excel_path, zip_path)
    os.remove(excel_path)

    session['zip_report_filename'] = zip_filename

    return zip_path



def clear_folder(folder_path):
    if os.path.exists(folder_path):
        for filename in os.listdir(folder_path):
            file_path = os.path.join(folder_path, filename)
            try:
                if os.path.isfile(file_path) or os.path.islink(file_path):
                    os.remove(file_path)
            except Exception as e:
                print(f"Failed to delete {file_path}: {e}")


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
    # uploads_folder = app.config['UPLOAD_FOLDER']
    if file.filename == '':
        flash('No file selected*', 'File')
        return redirect('/')
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(get_uploads_folder(), filename)
        file.save(filepath)
        print('successful file save')

        csv_to_excel(filepath) 
        clear_folder(get_uploads_folder())

        return redirect('/report-ready')
    flash('Invalid file type*', 'File')
    return redirect('/')

@app.route('/report-ready')
def report_ready():
    filename = session.get('zip_report_filename')
    # reports_folder = app.config['REPORTS_FOLDER']
    print(filename)
    if not filename:
        flash('You must upload a file before viewing the report.', 'File')
        clear_folder(get_reports_folder())
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

@app.route('/index_page')
def return_to_homepage():
    # reports_folder = app.config['REPORTS_FOLDER']
    clear_folder(get_reports_folder())
    return render_template('index.html')