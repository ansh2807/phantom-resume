"""
batch_processor.py — process a folder of resumes
"""

from pathlib import Path
from .resume_analyzer import ResumeAnalyzer
from .resume_improver import ResumeImprover
from .resume_injector import ResumeInjector


class BatchProcessor:
    def __init__(self, input_dir, output_dir, mode='safe'):
        self.input_dir = Path(input_dir)
        self.output_dir = Path(output_dir)
        self.mode = mode

    def run(self):
        self.output_dir.mkdir(parents=True, exist_ok=True)
        results = []
        for f in self.input_dir.glob('*.docx'):
            try:
                analysis = ResumeAnalyzer(str(f)).run()
                improvements = ResumeImprover(analysis).generate()
                injected = self.output_dir / (f.stem + '-injected' + f.suffix)
                injector = ResumeInjector(str(f), str(injected), mode=self.mode)
                inj_report = injector.run()
                results.append({
                    'file': f.name,
                    'score': analysis['score'],
                    'issues': len(analysis['issues']),
                    'suggestions': len(improvements),
                    'injected': str(injected),
                    'injection_steps': inj_report['steps'],
                })
            except Exception as e:
                results.append({'file': f.name, 'error': str(e)})
        return results
