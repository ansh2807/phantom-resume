#!/usr/bin/env python3
"""
PhantomResume — analyze, improve, inject resumes

Usage:
    python phantom_resume.py analyze <resume>
    python phantom_resume.py improve <resume>
    python phantom_resume.py inspect <resume>
    python phantom_resume.py inject <resume> [--mode safe|aggressive|nuclear] [--output <path>] [--pdf]
    python phantom_resume.py full <resume> [--mode MODE] [--output-dir DIR] [--pdf]
    python phantom_resume.py batch <input-dir> --output-dir <dir> [--mode MODE]
    python phantom_resume.py cover <letter.docx> [--mode MODE] [--output <path>]
"""

import sys
import argparse
from pathlib import Path
from colorama import init, Fore, Style

from core.resume_analyzer import ResumeAnalyzer
from core.resume_improver import ResumeImprover
from core.resume_injector import ResumeInjector
from core.resume_verifier import ResumeVerifier
from core.report_generator import ReportGenerator
from core.pdf_exporter import PDFExporter
from core.cover_letter import CoverLetterInjector
from core.batch_processor import BatchProcessor

from core.ats_fingerprint import fingerprint
from core.ats_profiles import get_profile, get_effectiveness
from core.cover_generator import generate_cover_letter
from core.diff_reporter import print_diff
from core.stealth_mode import randomize_injection_plan, compute_file_fingerprint
from core.tracker import SubmissionTracker
from core.portal_notes import generate_notes
from core.deep_metadata import run_all as run_deep_metadata

from core.ats_probe_runner import run_probe, save_probe_run
from core.ats_tuning import ATSTuning, INITIAL_WEIGHTS
from core.ats_extraction_analyzer import print_report as print_extraction_report

init(autoreset=True)


def cmd_analyze(args):
    p = Path(args.resume)
    if not p.exists():
        print(f"{Fore.RED}[!] Not found: {p}"); return 1
    print(f"{Fore.CYAN}[*] Analyzing {p.name}...")
    r = ResumeAnalyzer(str(p)).run()
    print(f"\n{Fore.GREEN}=== ATS SCORE: {r['score']}/100 ===\n")
    for k, v in r['breakdown'].items():
        bar = '█' * (v // 5) + '░' * (20 - v // 5)
        c = Fore.GREEN if v >= 70 else Fore.YELLOW if v >= 40 else Fore.RED
        print(f"  {k:15s} {c}{bar}{Style.RESET_ALL}  {v}")
    print(f"\n{Fore.CYAN}=== ISSUES ({len(r['issues'])}) ===")
    for i in r['issues']:
        c = Fore.RED if i['severity']=='high' else Fore.YELLOW if i['severity']=='medium' else Fore.CYAN
        print(f"  {c}[{i['severity'].upper()}]{Style.RESET_ALL} {i['msg']}")
    return 0


def cmd_improve(args):
    p = Path(args.resume)
    if not p.exists():
        print(f"{Fore.RED}[!] Not found"); return 1
    a = ResumeAnalyzer(str(p)).run()
    s = ResumeImprover(a).generate()
    if not s:
        print(f"{Fore.GREEN}[+] No improvements needed.")
        return 0
    print(f"\n{Fore.CYAN}=== SUGGESTIONS ({len(s)}) ===\n")
    for i, x in enumerate(s, 1):
        print(f"{Fore.YELLOW}{i}. {x['type']}{Style.RESET_ALL}")
        print(f"   {Fore.RED}Before:{Style.RESET_ALL} {x['before']}")
        print(f"   {Fore.GREEN}After: {Style.RESET_ALL} {x['after']}")
        print(f"   {Fore.CYAN}Why:{Style.RESET_ALL}   {x['reason']}\n")
    return 0


def cmd_inspect(args):
    p = Path(args.resume)
    if not p.exists():
        print(f"{Fore.RED}[!] Not found"); return 1
    e = ResumeVerifier(str(p)).extract()
    print(f"\n{Fore.CYAN}=== METADATA ===")
    for k, v in e.get('metadata', {}).items():
        print(f"  {k}: {v[:300]}")
    print(f"\n{Fore.CYAN}=== BODY ({len(e['all_text'])} chars) ===")
    print(e['all_text'][:3000])
    return 0


def cmd_inject(args):
    p = Path(args.resume)
    if not p.exists():
        print(f"{Fore.RED}[!] Not found"); return 1
    out = Path(args.output) if args.output else p.with_name(p.stem + '-injected' + p.suffix)
    print(f"{Fore.CYAN}[*] Injecting ({args.mode})...")
    r = ResumeInjector(str(p), str(out), mode=args.mode).run()
    for s in r['steps']:
        print(f"  {Fore.GREEN}✓{Style.RESET_ALL} {s}")
    print(f"\n{Fore.GREEN}[+] Wrote: {out}")

    if args.pdf:
        try:
            from core.pdf_exporter import PDFExporter
            pdf_out = out.with_suffix('.pdf')
            print(f"{Fore.CYAN}[*] Exporting PDF...")
            pr = PDFExporter(str(out), str(pdf_out), keep_metadata=True).run()
            print(f"  {Fore.GREEN}✓{Style.RESET_ALL} PDF: {pdf_out} (engine={pr['engine']}, paragraphs={pr['paragraphs']}, images={pr['images']})")
        except ImportError:
            print(f"{Fore.RED}[!] reportlab not installed")
        except Exception as ex:
            print(f"{Fore.RED}[!] PDF export failed: {ex}")

    from core.resume_verifier import ResumeVerifier
    print(f"\n{Fore.CYAN}[*] Verifying...")
    e = ResumeVerifier(str(out)).extract()
    print(f"\n{Fore.CYAN}=== WHAT ATS SEES ({len(e['all_text'])} chars) ===")
    print(e['all_text'][:1500])
    return 0


def cmd_full(args):
    p = Path(args.resume)
    if not p.exists():
        print(f"{Fore.RED}[!] Not found"); return 1
    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    print(f"{Fore.CYAN}[1/5] Analyze...")
    a = ResumeAnalyzer(str(p)).run()
    print(f"{Fore.CYAN}[2/5] Improve...")
    s = ResumeImprover(a).generate()
    print(f"{Fore.CYAN}[3/5] Inject ({args.mode})...")
    inj_path = out_dir / (p.stem + '-injected' + p.suffix)
    r = ResumeInjector(str(p), str(inj_path), mode=args.mode).run()
    for step in r['steps']:
        print(f"  ✓ {step}")

    print(f"{Fore.CYAN}[4/5] Verify...")
    e = ResumeVerifier(str(inj_path)).extract()

    print(f"{Fore.CYAN}[5/5] Report...")
    ReportGenerator(a, s, r, e, str(p)).save(str(out_dir / 'report.html'))

    if args.pdf:
        try:
            pdf_out = inj_path.with_suffix('.pdf')
            PDFExporter(str(inj_path), str(pdf_out)).run()
            print(f"  ✓ PDF: {pdf_out}")
        except ImportError:
            print(f"  {Fore.RED}[!] reportlab missing")

    print(f"\n{Fore.GREEN}[+] Done.")
    print(f"  Resume: {inj_path}")
    print(f"  Report: {out_dir / 'report.html'}")
    print(f"  Score:  {a['score']}/100")
    return 0


def cmd_batch(args):
    print(f"{Fore.CYAN}[*] Batch processing {args.input_dir}...")
    r = BatchProcessor(args.input_dir, args.output_dir, args.mode).run()
    for x in r:
        if 'error' in x:
            print(f"  {Fore.RED}✗ {x['file']}: {x['error']}")
        else:
            print(f"  {Fore.GREEN}✓ {x['file']}: {x['score']}/100 → {x['injected']}")
    print(f"\n{Fore.GREEN}[+] {len(r)} files processed.")
    return 0


def cmd_cover_legacy(args):
    p = Path(args.resume)
    if not p.exists():
        print(f"{Fore.RED}[!] Not found"); return 1
    out = Path(args.output) if args.output else p.with_name(p.stem + '-injected' + p.suffix)
    print(f"{Fore.CYAN}[*] Cover letter injection ({args.mode})...")
    r = CoverLetterInjector(str(p), str(out), mode=args.mode).run()
    for s in r['steps']:
        print(f"  {Fore.GREEN}✓{Style.RESET_ALL} {s}")
    print(f"\n{Fore.GREEN}[+] Wrote: {out}")
    return 0


def cmd_ats(args):
    print(f"{Fore.CYAN}[*] Fingerprinting {args.url}...")
    ats = fingerprint(args.url)
    profile = get_profile(ats)
    eff = get_effectiveness(ats)
    print(f"\n{Fore.GREEN}ATS: {ats}{Style.RESET_ALL}")
    print(f"  LLM-based:        {'yes' if profile['llm_based'] else 'no'}")
    print(f"  Recommended mode: {profile['recommended_mode']}")
    print(f"  Priority channels: {', '.join(profile['priority_channels']) or '(none)'}")
    print(f"\n{Fore.CYAN}Per-channel effectiveness:")
    for k, v in eff.items():
        bar = '█' * int(v * 20) + '░' * (20 - int(v * 20))
        print(f"  {k:22s} {Fore.GREEN if v >= 0.5 else Fore.YELLOW if v >= 0.2 else Fore.RED}{bar}{Style.RESET_ALL}  {int(v*100)}%")
    print(f"\n{Fore.YELLOW}[*] Effectiveness percentages are heuristic estimates, not measured results.{Style.RESET_ALL}")
    return 0


def cmd_cover_generate(args):
    p = Path(args.resume)
    a = ResumeAnalyzer(str(p)).run()
    jd = Path(args.jd).read_text(errors='ignore') if args.jd else 'the role'
    text = generate_cover_letter(a, jd, template=args.template)
    out = Path(args.output) if args.output else p.with_name(p.stem + '-cover.txt')
    out.write_text(text, encoding='utf-8')
    print(f"{Fore.GREEN}[+] Cover letter: {out}")
    if args.inject:
        try:
            from docx import Document
            doc = Document()
            for para in text.split('\n\n'):
                if para.strip():
                    doc.add_paragraph(para.strip())
            docx_out = out.with_suffix('.docx')
            doc.save(str(docx_out))
            injected_out = out.with_name(out.stem + '-injected.docx')
            inj = CoverLetterInjector(str(docx_out), str(injected_out), mode=args.inject).run()
            print(f"{Fore.GREEN}[+] Cover letter injected: {injected_out}")
            for s in inj['steps']:
                print(f"    ✓ {s}")
        except ImportError:
            print(f"{Fore.RED}[!] python-docx not installed")
    return 0


def cmd_diff(args):
    if not Path(args.original).exists() or not Path(args.injected).exists():
        print(f"{Fore.RED}[!] file not found"); return 1
    print_diff(args.original, args.injected)
    return 0


def cmd_stealth(args):
    p = Path(args.resume)
    out = Path(args.output) if args.output else p.with_name(p.stem + '-stealth' + p.suffix)
    plan = randomize_injection_plan(args.mode, lang='en')
    print(f"{Fore.CYAN}[*] Stealth plan ({args.mode}): {', '.join(plan)}{Style.RESET_ALL}")

    from core.resume_injector import ResumeInjector
    inj = ResumeInjector(str(p), str(out), mode=args.mode)
    # NEW: override the mode-specific channel list
    inj.channel_plan = plan
    r = inj.run()

    for s in r['steps']:
        print(f"  {Fore.GREEN}✓{Style.RESET_ALL} {s}")
    for e in r.get('errors', []):
        print(f"  {Fore.RED}✗{Style.RESET_ALL} {e}")

    h = compute_file_fingerprint(str(out))
    print(f"\n{Fore.GREEN}[+] Wrote: {out}{Style.RESET_ALL}")
    print(f"  File hash: {h}")
    print(f"  Applied channels: {', '.join(plan)}")
    return 0


def cmd_track(args):
    t = SubmissionTracker(args.db)
    if args.add:
        company, role, ats, mode, variant = args.add
        t.record(company, role, ats, mode, variant, '', '', '')
        print(f"{Fore.GREEN}[+] Recorded submission")
    elif args.status:
        sid, status = args.status
        t.update_status(int(sid), status)
        print(f"{Fore.GREEN}[+] Updated #{sid} → {status}")
    else:
        rep = t.effectiveness_report()
        print(f"\n{Fore.CYAN}=== EFFECTIVENESS REPORT ==={Style.RESET_ALL}")
        for section, key in [('By variant', 'variants'), ('By mode', 'modes'), ('By ATS', 'ats')]:
            print(f"\n{Fore.YELLOW}{section}:{Style.RESET_ALL}")
            for row in rep[key]:
                name = row.get('variant') or row.get('mode') or row.get('ats')
                print(f"  {name}: {row['positives']}/{row['total']} ({row['rate']:.0%})")
    return 0


def cmd_notes(args):
    text = generate_notes(variant=args.variant, style=args.style)
    print(text)
    return 0


def cmd_deep(args):
    p = Path(args.resume)
    if not p.exists():
        print(f"{Fore.RED}[!] not found"); return 1
    results = run_deep_metadata(str(p))
    for channel, ok in results.items():
        print(f"  {Fore.GREEN if ok else Fore.YELLOW}{'✓' if ok else '–'}{Style.RESET_ALL} {channel}")
    return 0


def cmd_langs(args):
    from core.payloads_i18n import I18N_INSTRUCTIONS
    print(f"{Fore.CYAN}Available languages: {', '.join(I18N_INSTRUCTIONS.keys())}{Style.RESET_ALL}")
    for lang, instrs in I18N_INSTRUCTIONS.items():
        print(f"\n[{lang}] {instrs[0][:120]}...")
    return 0


def cmd_cover(args):
    p = Path(args.resume)
    if not p.exists():
        print(f"{Fore.RED}[!] Not found"); return 1

    if not args.jd:
        # legacy: raw injection of an existing cover letter
        print(f"{Fore.YELLOW}[*] Legacy mode: injecting cover letter metadata only.{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}    Use --jd <file> --inject <mode> for generated + injected cover.{Style.RESET_ALL}")
        out = Path(args.output) if args.output else p.with_name(p.stem + '-injected' + p.suffix)
        inj = CoverLetterInjector(str(p), str(out), mode=args.mode).run()
        for s in inj['steps']:
            print(f"  {Fore.GREEN}✓{Style.RESET_ALL} {s}")
        print(f"\n{Fore.GREEN}[+] Wrote: {out}")
        return 0

    # new: generate from resume + JD
    a = ResumeAnalyzer(str(p)).run()
    jd = Path(args.jd).read_text(errors='ignore')
    text = generate_cover_letter(a, jd, template=args.template)
    out = Path(args.output) if args.output else p.with_name(p.stem + '-cover.txt')
    out.write_text(text, encoding='utf-8')
    print(f"{Fore.GREEN}[+] Cover letter: {out}")
    if args.inject:
        from docx import Document
        doc = Document()
        for para in text.split('\n\n'):
            if para.strip():
                doc.add_paragraph(para.strip())
        docx_out = out.with_suffix('.docx')
        doc.save(str(docx_out))
        injected_out = out.with_name(out.stem + '-injected.docx')
        inj = CoverLetterInjector(str(docx_out), str(injected_out), mode=args.inject).run()
        print(f"{Fore.GREEN}[+] Injected: {injected_out}")
    return 0


def cmd_probe(args):
    from pathlib import Path
    import datetime

    print(f"{Fore.CYAN}[*] Running probe: {args.ats}{Style.RESET_ALL}")
    if args.probe_only:
        print(f"{Fore.YELLOW}[*] PROBE-ONLY MODE — no form filling, upload, or submission{Style.RESET_ALL}")
    result = run_probe(args.ats, args.resume, args.url, verbose=True,
                       probe_only=args.probe_only)

    # check for error before proceeding
    if result.get('error'):
        print(f"\n{Fore.RED}[!] Probe failed: {result['error']}{Style.RESET_ALL}")
        if result.get('submit', {}).get('errors'):
            for e in result['submit']['errors']:
                print(f"    {e}")
        print(f"\n{Fore.YELLOW}[*] No tuning update — probe did not complete.{Style.RESET_ALL}")
        return 1

    submit = result.get('submit', {})
    if args.probe_only:
        print(f"\n{Fore.GREEN}[+] Probe-only inspection completed{Style.RESET_ALL}")
        print(f"  Form found: {submit.get('form_found', False)}")
        print(f"  File input found: {submit.get('file_input_found', False)}")
        print(f"  Final URL: {submit.get('final_url', '(none)')}")
        print(f"  {submit.get('note', '')}")
        print("  No tuning update — page inspection does not test resume extraction.")
        out_dir = Path(args.output_dir or './probe_runs')
        out_dir.mkdir(parents=True, exist_ok=True)
        ts = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        out_path = out_dir / f"{args.ats}_probe_only_{ts}.json"
        save_probe_run(result, str(out_path))
        print(f"\n{Fore.GREEN}[+] Probe saved: {out_path}{Style.RESET_ALL}")
        return 0 if submit.get('form_found') and submit.get('file_input_found') else 1

    if not submit.get('submitted'):
        print(f"\n{Fore.RED}[!] Probe did not submit (no confirmation captured){Style.RESET_ALL}")
        for e in submit.get('errors', []):
            print(f"    {e}")
        return 1

    print(f"\n{Fore.GREEN}[+] Submission confirmed{Style.RESET_ALL}")
    print(f"  Final URL: {submit.get('final_url', '(none)')}")
    print(f"  Confirmation preview: {submit.get('confirmation_text', '')[:200]}")
    print(f"  Email hint: {submit.get('confirmation_email_hint', '')}")

    print_extraction_report(result.get('ats_extraction_analysis', {}))

    tuning = ATSTuning()
    tuning.update_from_probe(args.ats, result)
    tuning.print_summary(args.ats)

    out_dir = Path(args.output_dir or './probe_runs')
    out_dir.mkdir(exist_ok=True)
    ts = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    out_path = out_dir / f"{args.ats}_{ts}.json"
    save_probe_run(result, str(out_path))
    print(f"\n{Fore.GREEN}[+] Probe saved: {out_path}{Style.RESET_ALL}")
    return 0


def cmd_tuning(args):
    t = ATSTuning()
    if args.reset:
        t.weights = {k: dict(v) for k, v in INITIAL_WEIGHTS.items()}
        t.save()
        print(f"{Fore.GREEN}[+] tuning reset to defaults{Style.RESET_ALL}")
        return 0
    t.print_summary(args.ats or 'unknown')
    return 0


def main():
    p = argparse.ArgumentParser(description='PhantomResume v3')
    sub = p.add_subparsers(dest='cmd', required=True)

    a = sub.add_parser('analyze'); a.add_argument('resume'); a.set_defaults(func=cmd_analyze)
    i = sub.add_parser('improve'); i.add_argument('resume'); i.set_defaults(func=cmd_improve)
    ins = sub.add_parser('inspect'); ins.add_argument('resume'); ins.set_defaults(func=cmd_inspect)

    inj = sub.add_parser('inject')
    inj.add_argument('resume')
    inj.add_argument('--mode', choices=['safe','aggressive','nuclear'], default='safe')
    inj.add_argument('--output')
    inj.add_argument('--pdf', action='store_true')
    inj.set_defaults(func=cmd_inject)

    f = sub.add_parser('full')
    f.add_argument('resume')
    f.add_argument('--mode', choices=['safe','aggressive','nuclear'], default='safe')
    f.add_argument('--output-dir', default='./phantom_output')
    f.add_argument('--pdf', action='store_true')
    f.set_defaults(func=cmd_full)

    b = sub.add_parser('batch')
    b.add_argument('input_dir')
    b.add_argument('--output-dir', required=True)
    b.add_argument('--mode', choices=['safe','aggressive','nuclear'], default='safe')
    b.set_defaults(func=cmd_batch)

    co = sub.add_parser('cover')
    co.add_argument('resume')
    co.add_argument('--jd')
    co.add_argument('--template', default='professional')
    co.add_argument('--output')
    co.add_argument('--inject', choices=['safe','aggressive','nuclear'], help='inject mode (requires --jd)')
    co.add_argument('--mode', choices=['safe','aggressive','nuclear'], help='legacy: inject existing cover letter')
    co.set_defaults(func=cmd_cover)

    a = sub.add_parser('ats'); a.add_argument('url'); a.set_defaults(func=cmd_ats)

    d = sub.add_parser('diff')
    d.add_argument('original')
    d.add_argument('injected')
    d.set_defaults(func=cmd_diff)

    s = sub.add_parser('stealth')
    s.add_argument('resume')
    s.add_argument('--mode', default='aggressive')
    s.add_argument('--output')
    s.set_defaults(func=cmd_stealth)

    tr = sub.add_parser('track')
    tr.add_argument('--db', default='submissions.db')
    tr.add_argument('--add', nargs=5, metavar=('COMPANY','ROLE','ATS','MODE','VARIANT'))
    tr.add_argument('--status', nargs=2, metavar=('ID','STATUS'))
    tr.set_defaults(func=cmd_track)

    n = sub.add_parser('notes')
    n.add_argument('--variant', default='A')
    n.add_argument('--style', default='brief')
    n.set_defaults(func=cmd_notes)

    dp = sub.add_parser('deep')
    dp.add_argument('resume')
    dp.set_defaults(func=cmd_deep)

    l = sub.add_parser('langs'); l.set_defaults(func=cmd_langs)

    # probe command
    pr = sub.add_parser('probe', help='probe an ATS with a test resume')
    pr.add_argument('ats', choices=['greenhouse', 'lever'])
    pr.add_argument('resume')
    pr.add_argument('--url', required=True, help='test portal URL only (safety guard)')
    pr.add_argument('--output-dir')
    pr.add_argument('--probe-only', action='store_true',
                    help='inspect form controls without filling, uploading, or submitting')
    pr.set_defaults(func=cmd_probe)

    # tuning command
    tu = sub.add_parser('tuning', help='view/reset per-ATS channel weights')
    tu.add_argument('ats', nargs='?')
    tu.add_argument('--reset', action='store_true')
    tu.set_defaults(func=cmd_tuning)

    args = p.parse_args()
    return args.func(args)


if __name__ == '__main__':
    sys.exit(main())