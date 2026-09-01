import subprocess
import re

with open('index.html', 'r') as f:
    html = f.read()

views = [
    ('view-dashboard', 'shot_dashboard.png'),
    ('view-stt-registry', 'shot_stt_registry.png'),
    ('view-stt-benchmark', 'shot_stt_benchmark.png'),
    ('view-filler-explorer', 'shot_filler_explorer.png'),
    ('view-tts-showcase', 'shot_tts_showcase.png')
]

for view_id, out_file in views:
    temp_html = html
    # Remove active class from all sections
    temp_html = re.sub(r'class="view-section active"', 'class="view-section"', temp_html)
    
    # Add active class to the specific section
    temp_html = re.sub(f'class="view-section" id="{view_id}"', f'class="view-section active" id="{view_id}"', temp_html)
    
    with open('temp.html', 'w') as f:
        f.write(temp_html)
    
    cmd = [
        'google-chrome', '--headless=new', '--screenshot=' + out_file,
        '--window-size=1200,1000', '--virtual-time-budget=5000',
        'file:///home/ansinitro/AITU/scientific-practice/temp.html'
    ]
    subprocess.run(cmd)
    print(f"Captured {out_file}")

