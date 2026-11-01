"""Evaluate Part 1.   python -m eval.run_eval --version final --runs 3   ->  eval/results.md
Metrics: valid_output, gate_correct, count_ok (3-6), warning_free, consistency (vocab Jaccard across runs), count stability.
Note: at temperature 0 consistency mostly measures provider non-determinism."""
import argparse, itertools, json, statistics
from collections import Counter
from pathlib import Path
from backend.rules import _toks, check_decomposition
from backend.stages.analyze import analyze_question
from backend.stages.decompose import decompose

def one_run(q, version):
    try:
        a = analyze_question(q, version)
        d = decompose(q, a, version) if a.researchable else None
        return {"ok": True, "researchable": a.researchable, "d": d, "warns": check_decomposition(d, a)[1] if d else []}
    except Exception as e:
        return {"ok": False, "error": str(e)[:200]}

def vocab(run):
    return set().union(*[_toks(s.question) for s in run["d"].sub_questions])

def jac(a, b):
    return len(a & b) / len(a | b) if (a | b) else 1.0

def evaluate(cases, runs, version):
    pct = lambda a, b: f"{100 * a / b:.0f}%" if b else "n/a"
    rows, tot = [], Counter()
    for c in cases:
        rs = [one_run(c["question"], version) for _ in range(runs)]
        ok = [r for r in rs if r["ok"]]
        gate = [r["researchable"] == c["expect_researchable"] for r in ok]
        dec = [r for r in ok if r["d"]]
        count_ok = [3 <= len(r["d"].sub_questions) <= 6 for r in dec]
        warn_free = [not r["warns"] for r in dec]
        cons = statistics.mean(jac(vocab(a), vocab(b)) for a, b in itertools.combinations(dec, 2)) if len(dec) > 1 else None
        stab = Counter(len(r["d"].sub_questions) for r in dec).most_common(1)[0][1] / len(dec) if dec else None
        rows.append((c, len(ok), len(rs), gate, count_ok, warn_free, cons, stab))
        tot.update(valid=len(ok), runs=len(rs), gate=sum(gate), gate_n=len(gate), count=sum(count_ok),
                   count_n=len(count_ok), warn=sum(warn_free), warn_n=len(warn_free))
    out = [f"# Part 1 evaluation (prompt: {version}, runs per case: {runs})\n",
           "| Case | Category | Valid | Gate correct | Count 3-6 | Warning-free | Consistency | Count stability |",
           "|---|---|---|---|---|---|---|---|"]
    f = lambda x: pct(sum(x), len(x))
    for c, v, n, g, co, w, cons, stab in rows:
        out.append(f"| {c['id']} | {c['category']} | {v}/{n} | {f(g)} | {f(co)} | {f(w)} | "
                   f"{'n/a' if cons is None else f'{cons:.2f}'} | {'n/a' if stab is None else f'{stab:.0%}'} |")
    out += ["", "## Summary",
            f"- Valid structured output: {pct(tot['valid'], tot['runs'])}",
            f"- Researchable gate accuracy: {pct(tot['gate'], tot['gate_n'])}",
            f"- Sub-question count in range: {pct(tot['count'], tot['count_n'])}",
            f"- Warning-free decompositions: {pct(tot['warn'], tot['warn_n'])}"]
    return "\n".join(out)

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--version", default="final"); ap.add_argument("--runs", type=int, default=3)
    a = ap.parse_args()
    md = evaluate(json.loads(Path("eval/cases.json").read_text(encoding="utf-8")), a.runs, a.version)
    Path("eval/results.md").write_text(md, encoding="utf-8")
    print(md)
