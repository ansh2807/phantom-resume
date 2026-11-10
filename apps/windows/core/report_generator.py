"""
report_generator.py — HTML report
"""

from pathlib import Path
from datetime import datetime


HTML = '''<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>PhantomResume Report</title>
<style>
  body{font-family:-apple-system,sans-serif;background:#0a0a0a;color:#e0e0e0;
       max-width:1200px;margin:40px auto;padding:0 20px}
  h1{color:#00ff88}
  h2{color:#00ff88;border-bottom:1px solid #333;padding-bottom:8px}
  .score-box{text-align:center;margin:40px 0}
  .score-num{font-size:72px;font-weight:bold}
  .score-num.good{color:#00ff88}.score-num.mid{color:#ffaa00}.score-num.bad{color:#ff4444}
  .bar{display:inline-block;width:200px;height:16px;background:#222;
       border-radius:8px;overflow:hidden;vertical-align:middle}
  .bar-fill{height:100%}
  .bar-fill.good{background:#00ff88}.bar-fill.mid{background:#ffaa00}.bar-fill.bad{background:#ff4444}
  .section-row{margin:12px 0}
  .section-name{display:inline-block;width:180px}
  .issue{background:#1a1a1a;padding:12px;margin:8px 0;border-left:4px solid}
  .issue.high{border-color:#ff4444}.issue.medium{border-color:#ffaa00}
  .issue .severity{font-size:11px;text-transform:uppercase;opacity:.8}
  .suggestion{background:#1a1a1a;padding:16px;margin:12px 0;border-left:4px solid #00ff88}
  .before{color:#ff8888}.after{color:#88ff88}
  .reason{color:#888;font-size:13px;font-style:italic}
  .extracted-text{background:#111;padding:20px;border-radius:8px;
                  white-space:pre-wrap;font-family:monospace;font-size:13px;
                  max-height:400px;overflow-y:auto}
  .meta-table{width:100%;border-collapse:collapse}
  .meta-table td{padding:6px;border-bottom:1px solid #222;vertical-align:top}
  .meta-table td:first-child{width:150px;color:#888}
  .timestamp{color:#666;font-size:13px}
</style></head><body>
<h1>🛸 PhantomResume Report</h1>
<p class="timestamp">Generated {{timestamp}}</p>
<p class="timestamp">Source: {{source_file}}</p>
<div class="score-box">
  <div class="score-num {{score_class}}">{{score}}</div>
  <div>out of 100</div>
</div>
<h2>Score Breakdown</h2>
{{breakdown_html}}
<h2>Issues ({{issue_count}})</h2>
{{issues_html}}
<h2>Improvements ({{suggestion_count}})</h2>
{{suggestions_html}}
<h2>Injection — Mode: {{injection_mode}}</h2>
{{injection_html}}
<h2>What ATS Sees</h2>
<h3>Metadata</h3>
<table class="meta-table">{{metadata_html}}</table>
<h3>Extracted Text</h3>
<div class="extracted-text">{{extracted_text}}</div>
</body></html>'''


class ReportGenerator:
    def __init__(self, analysis, improvements, injection_report, extracted, source_file):
        self.a = analysis
        self.i = improvements
        self.inj = injection_report
        self.e = extracted
        self.src = source_file

    def _breakdown(self):
        h = ''
        for k, v in self.a['breakdown'].items():
            cls = 'good' if v >= 70 else 'mid' if v >= 40 else 'bad'
            h += (f'<div class="section-row"><span class="section-name">{k}</span> '
                  f'<span class="bar"><span class="bar-fill {cls}" style="width:{v}%"></span></span> '
                  f'{v}</div>')
        return h

    def _issues(self):
        if not self.a['issues']:
            return '<p style="color:#00ff88">✓ No issues</p>'
        return ''.join(f'<div class="issue {i["severity"]}">'
                       f'<div class="severity">{i["severity"]}</div>{i["msg"]}</div>'
                       for i in self.a['issues'])

    def _suggestions(self):
        if not self.i:
            return '<p style="color:#00ff88">✓ No improvements</p>'
        return ''.join(f'<div class="suggestion">'
                       f'<div><strong>{s["type"]}</strong></div>'
                       f'<div class="before">Before: {s["before"]}</div>'
                       f'<div class="after">After: {s["after"]}</div>'
                       f'<div class="reason">{s["reason"]}</div></div>'
                       for s in self.i)

    def _injection(self):
        if not self.inj or not self.inj.get('steps'):
            return '<p>None</p>'
        return '<ul>' + ''.join(f'<li>{s}</li>' for s in self.inj['steps']) + '</ul>'

    def _meta(self):
        h = ''
        for k, v in self.e.get('metadata', {}).items():
            h += f'<tr><td>{k}</td><td>{v[:500]}</td></tr>'
        return h or '<tr><td colspan="2">(empty)</td></tr>'

    def save(self, path):
        s = self.a['score']
        cls = 'good' if s >= 70 else 'mid' if s >= 40 else 'bad'
        h = HTML
        h = h.replace('{{timestamp}}', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        h = h.replace('{{source_file}}', self.src)
        h = h.replace('{{score}}', str(s))
        h = h.replace('{{score_class}}', cls)
        h = h.replace('{{breakdown_html}}', self._breakdown())
        h = h.replace('{{issue_count}}', str(len(self.a['issues'])))
        h = h.replace('{{issues_html}}', self._issues())
        h = h.replace('{{suggestion_count}}', str(len(self.i)))
        h = h.replace('{{suggestions_html}}', self._suggestions())
        h = h.replace('{{injection_mode}}', self.inj.get('mode', 'none'))
        h = h.replace('{{injection_html}}', self._injection())
        h = h.replace('{{metadata_html}}', self._meta())
        h = h.replace('{{extracted_text}}', self.e.get('all_text', '')[:10000])
        Path(path).write_text(h, encoding='utf-8')