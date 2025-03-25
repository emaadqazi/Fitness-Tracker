import os
import subprocess
from datetime import datetime

# Create reports directory if it doesn't exist
os.makedirs('reports/test_reports', exist_ok=True)

# Generate date-based filename
report_date = datetime.now().strftime('%Y-%m-%d')
report_path = f'reports/test_reports/{report_date}_report.html'

# Run pytest with HTML report generation
cmd = f'python -m pytest --html={report_path} --self-contained-html'
print(f"Running command: {cmd}")

# Use shell=True to run the command 
result = subprocess.run(cmd, shell=True)

if result.returncode == 0:
    print(f"Tests passed! Report generated at: {report_path}")
else:
    print(f"Tests failed with return code: {result.returncode}")