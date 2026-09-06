"""Generate a static local starting folder from an existing handoff store."""
import argparse
import html
import json
from pathlib import Path
from urllib.parse import quote

import handoff as h

HERE = Path(__file__).resolve().parent
DEFAULT_STORE = HERE / 'physics' / 'store'
MVP_BRIEF = HERE / 'physics' / 'mvp-brief.json'
DEFAULT_TARGET = h.read_json(HERE / 'physics' / 'index.json')['target']


def resolve_target(store, target):
    if target:
        return target
    keys = sorted(h.records(store, 'targets'))
    h.require(len(keys) == 1, 'specify --target; store does not contain exactly one target')
    return keys[0]


def is_default_store(store):
    return store is None or Path(store).resolve() == DEFAULT_STORE.resolve()


def is_default_target(target):
    return target is None or target == DEFAULT_TARGET


def href_path(path):
    return '/'.join(quote(part, safe='') for part in path.split('/'))


def md_safe(text):
    return h.md_data(text)


def attempt_context(key, attempt):
    return '%s; method: %s; attempt %s' % (
        attempt['provenance']['contributor'], attempt['method'], key)


def evidence_label(key, attempt, ref):
    return '%s %s (%s)' % (ref['role'], ref['path'], attempt_context(key, attempt))


def assessment_label(key, assessment, attempts):
    contributor = attempts[assessment['attempt']]['provenance']['contributor']
    return '%s assessment by %s of %s (attempt %s)' % (
        assessment['status'], assessment['reviewer'], contributor, assessment['attempt'])


def local_links(target, view):
    items = [('Readable Markdown handoff', 'C/handoff.md'),
             ('Structured JSON handoff', 'D/state.json'),
             ('Use and return instructions', 'USE.md'),
             ('Editable submission template', 'submission-template.json'),
             ('Optional condition A', 'A/assignment.json'),
             ('Optional condition B', 'B/assignment.json')]
    for name in target.get('inputs', {}).get('files', {}):
        items.append(('Source file ' + name, 'C/inputs/' + name))
    attempts = view['attempts']
    for key, attempt in attempts.items():
        items.append(('Attempt record (%s)' % attempt_context(key, attempt),
                      'C/history/attempt-' + key + '.json'))
        for ref in attempt['evidence']:
            items.append((evidence_label(key, attempt, ref), 'C/history/' + ref['sha256']))
    for key, assessment in view['assessments'].items():
        items.append((assessment_label(key, assessment, attempts),
                      'C/history/assessment-' + key + '.json'))
    return items


def primary_links(target, view):
    keep = {'C/handoff.md', 'D/state.json', 'USE.md', 'submission-template.json'}
    items = [('Markdown fallback START.md', 'START.md')]
    items.extend(item for item in local_links(target, view)
                 if item[1] in keep or item[1].startswith('C/inputs/'))
    attempts = view['attempts']
    for key, assessment in view['assessments'].items():
        items.append((assessment_label(key, assessment, attempts),
                      'C/history/assessment-' + key + '.json'))
    for key, attempt in attempts.items():
        for ref in attempt['evidence']:
            if ref['role'] == 'result':
                items.append((evidence_label(key, attempt, ref), 'C/history/' + ref['sha256']))
    return items


def ab_links():
    return [('Optional condition A', 'A/assignment.json'),
            ('Optional condition B', 'B/assignment.json')]


def owner_tool(packaged):
    if packaged:
        return 'python toolkit/handoff.py --store store'
    return 'python research/handoff.py --store PATH_TO_OWNER_STORE'


def return_guide(assignment, packaged=False, target=None):
    target_key = assignment['target']
    snap = assignment['base_snapshot']
    tool = owner_tool(packaged)
    checker = None
    if target is not None:
        checker = target.get('acceptance', {}).get('checker')
    if packaged:
        where = ('Owner commands, from this package directory. This public-reference demonstration '
                 'includes toolkit/ and store/ for the already-public default example only.')
        provenance = ('This folder is the fixed public-reference demonstration package. It is not a '
                      'privacy guarantee for arbitrary stores, not a security sandbox, and not '
                      'independent human certification of science or identity.')
    else:
        where = ('Owner commands, from the source repository. This export does not include toolkit/ or store/. '
                 'The owner keeps the original handoff.py, fixture_checker.py, and the matching owner store '
                 'that produced this export. PATH_TO_OWNER_STORE is that store '
                 '(for the default physics example: research/physics/store). '
                 'Custom exports are not a public-reference demonstration.')
        provenance = ('This folder is a starting export, not a self-contained public-reference package.')
    if checker == 'external-review-pending':
        fixture_line = ('Unavailable external physics checking is not fixture verification. '
                        'fixture_checker.py only checks the software-mechanics graph fixture and '
                        'must refuse this physics target. SOFTWARE-MECHANICS synthetic returns are '
                        'import tests, not research evidence.')
    else:
        fixture_line = ('Unavailable external physics checking is not fixture verification. '
                        'fixture_checker.py only checks the software-mechanics graph fixture. '
                        'SOFTWARE-MECHANICS synthetic returns are import tests, not research evidence.')
    return '\n'.join([
        provenance,
        'Give the recipient the WHOLE folder, not just the copied prompt. Copied text does not carry original evidence bytes.',
        'Preserve target %s and base_snapshot %s, and keep the recorded scope.' % (target_key, snap),
        'Create a new return folder with submission.json (copy submission-template.json) plus original result/source attachments named in evidence paths. Return that folder to the owner.',
        where,
        tool + ' submit RETURN_FOLDER/submission.json',
        tool + ' inspect ' + target_key,
        tool + ' check ATTEMPT',
        tool + ' assess ATTEMPT --reviewer REVIEWER --status withhold --rationale TEXT --limitations TEXT',
        'For external-review-pending physics targets, check must refuse with: external checker not registered. Then a distinct reviewer records withhold. Do not invent a physics checker or accept without a passing independent check.',
        'A stale base_snapshot requires owner reconciliation and a new request_id; do not rebase silently.',
        'A candidate cannot choose or weaken the checker. Submissions cannot set checker, commands, timeouts, or thresholds. Do not execute submitted code.',
        fixture_line,
    ])


def use_md(assignment, packaged=False, target=None):
    return '\n'.join([
        '# Use and return this folder',
        '',
        '## Read',
        '',
        'Open `index.html` or `START.md`. Keep every file in this folder together.',
        '',
        '## Return original evidence',
        '',
        return_guide(assignment, packaged, target).replace('\n', '\n\n'),
        '',
        'Do not add a form, server, or accounts. Do not run unknown submitted code.',
        '',
    ]) + '\n'


def resource_lines(resources):
    if 'fixture_model_tokens' in resources:
        return ('Fixture software caps only: fixture_model_tokens=%s, fixture_wall_seconds=%s, '
                'model=%s, external_search=%s. These are not a research budget.'
                % (resources['fixture_model_tokens'], resources['fixture_wall_seconds'],
                   resources['model'], resources['external_search']))
    return ('Model cap: unassigned. Compute cap: unassigned. %s. '
            'Reading the handoff and inspecting existing evidence may proceed; that is not an '
            'authorized full scientific run or controlled evaluation.'
            % resources['limits'])


def submission_template(target_key, target, assignment):
    evidence = [{'path': 'result.json', 'role': 'result',
                 'source': 'locally attached original bytes', 'locator': 'entire file'}]
    for name in target.get('inputs', {}).get('files', {}):
        evidence.append({'path': name, 'role': 'source',
                         'source': 'copy original bytes next to the submission', 'locator': 'entire file'})
    return {
        'request_id': 'replace-with-a-new-unique-id',
        'base_snapshot': assignment['base_snapshot'],
        'target': target_key,
        'method': 'Describe the method actually used.',
        'scope': target['scope'],
        'inputs': {},
        'environment': 'Describe the actual environment.',
        'budget': {'human_minutes': None, 'compute_usd': None},
        'outcome': 'completed',
        'observation': 'Record observations, including failures. Do not replace original evidence with a summary.',
        'interpretation': 'Record interpretation separately. Do not treat this as acceptance.',
        'retry_reason': 'State why this is a new request_id, or that it is replication.',
        'depends_on': [],
        'provenance': {
            'contributor': 'your-contributor-label',
            'model': 'your-model-or-none',
            'configuration': 'your-configuration',
            'source_locator': 'your-source-locator',
            'shared_roots': 'Disclose shared roots. Do not claim independence you do not have.',
        },
        'evidence': evidence,
    }


def recipient_prompt(target_key, target, brief, view, assignment, packaged=False):
    acc = target['acceptance']
    assessments = []
    for key, a in view['assessments'].items():
        assessments.append('- %s by %s (assessment %s): %s Limitations: %s'
                           % (a['status'], a['reviewer'], key, a['rationale'], a['limitations']))
    attempts = []
    for key, a in view['attempts'].items():
        attempts.append('- %s (%s, attempt %s): %s'
                        % (a['method'], a['outcome'], key, a['observation']))
    paths = '\n'.join('  ' + path for _, path in local_links(target, view))
    template = json.dumps(submission_template(target_key, target, assignment),
                          ensure_ascii=False, indent=2)
    return '\n'.join([
        'Continue this local research handoff from the exported folder you were given.',
        '',
        'This static page cannot launch an agent, mutate the store, verify science, or enforce resource budgets.',
        '',
        'Target digest: ' + target_key,
        'Target id: ' + target['id'],
        'Owner: ' + target['owner'],
        'Base snapshot: ' + assignment['base_snapshot'],
        'Question: ' + target['question'],
        'Scope: ' + target['scope'],
        'Assumptions: ' + target['assumptions'],
        'stop_condition: ' + target['stop_condition'],
        'Acceptance checker: ' + str(acc['checker']),
        'Acceptance checker pin: ' + str(acc['checker_sha256']),
        'Acceptance criterion: ' + str(acc['criterion']),
        "A submission cannot change the checker's pinned acceptance.",
        '',
        resource_lines(assignment['resources']),
        '',
        'Current observed brief: ' + brief['current_assessment'],
        'Unresolved: ' + brief['unresolved_checks'],
        'ONE next action: ' + brief['proposed_next_check'],
        '',
        'Available prior attempts (preserve failures and disputes; do not drop withhold/challenge/narrow):',
        '\n'.join(attempts) if attempts else '- none in this export',
        '',
        'Exact assessments:',
        '\n'.join(assessments) if assessments else '- none in this export',
        '',
        'Package-relative paths (real local paths, not URL-encoded hrefs):',
        paths,
        '',
        return_guide(assignment, packaged, target),
        'Do not paste a sealed attempt JSON from C/history. Remove each evidence sha256; submit rejects that extra field.',
        'Use local attached paths. Include exactly one result role. Provenance keys must be exactly contributor, model, configuration, source_locator, shared_roots.',
        'Use a new unique request_id and the exported base_snapshot below.',
        'Do not fabricate review results or assigned costs. Budget fields that were not measured stay null.',
        'Do not run a full scientific evaluation unless the owner assigned execution limits.',
        '',
        'Valid submission template:',
        template,
    ])


def fence(text):
    ticks = '```'
    while ticks in text:
        ticks += '`'
    return ticks + '\n' + text + '\n' + ticks + '\n'


def html_links(items):
    esc = html.escape
    return '\n'.join('<li><a href="%s">%s</a></li>'
                     % (esc(href_path(path), quote=True), esc(label))
                     for label, path in items)


def md_links(items):
    return '\n'.join('- [%s](%s)' % (md_safe(label), href_path(path)) for label, path in items)


def render_html(target_key, target, brief, view, assignment, packaged=False):
    esc = html.escape
    attempts = []
    for key, a in view['attempts'].items():
        path = 'C/history/attempt-' + key + '.json'
        attempts.append('<li><a href="%s">%s</a> — %s. %s</li>'
                        % (esc(href_path(path), quote=True), esc(attempt_context(key, a)),
                           esc(a['outcome']), esc(a['observation'])))
    assessments = []
    for key, a in view['assessments'].items():
        path = 'C/history/assessment-' + key + '.json'
        assessments.append('<li><a href="%s">%s</a>: %s</li>'
                           % (esc(href_path(path), quote=True),
                              esc(assessment_label(key, a, view['attempts'])),
                              esc(a['rationale'])))
    details = [
        ('Owner', target['owner']),
        ('Scope', target['scope']),
        ('Assumptions', target['assumptions']),
        ('stop_condition', target['stop_condition']),
        ('Unresolved checks', brief['unresolved_checks']),
        ('Target digest', target_key),
        ('Base snapshot', assignment['base_snapshot']),
        ('Resources', json.dumps(assignment['resources'], ensure_ascii=False, sort_keys=True)),
        ('Acceptance', json.dumps(target['acceptance'], ensure_ascii=False, sort_keys=True)),
    ]
    if assignment.get('curated_information_sha256'):
        details.append(('Curated information digest', assignment['curated_information_sha256']))
    detail_rows = '\n'.join('<li>%s: <code>%s</code></li>' % (esc(k), esc(v)) for k, v in details)
    prompt = recipient_prompt(target_key, target, brief, view, assignment, packaged)
    evidence = [item for item in local_links(target, view)
                if item not in primary_links(target, view) and item[1] not in {p for _, p in ab_links()}]
    return '''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Local research starting page</title>
<style>
body { font: 18px/1.45 sans-serif; max-width: 46rem; margin: 1.5rem auto; padding: 0 1rem; }
textarea { width: 100%%; min-height: 18rem; font: 14px/1.4 monospace; }
code, textarea, a { overflow-wrap: anywhere; word-break: break-word; }
.note { background: #f4f4f4; padding: 0.75rem 1rem; }
</style>
</head>
<body>
<p class="note">This is a static local folder. It cannot launch an agent, mutate the store, verify science, or enforce resource budgets. You do not need researchers or command-line tools to read the question, the observed result, and the next step.</p>
<h1>The question</h1>
<p>%s</p>
<h2>What was already checked</h2>
<p>%s</p>
<h2>One next action</h2>
<p>%s</p>
<h2>Open the local files</h2>
<ul>
%s
</ul>
<h2>Use and return this folder</h2>
<p>Give the recipient the WHOLE folder, not just the copied prompt. Open <a href="USE.md">USE.md</a> and edit <a href="submission-template.json">submission-template.json</a> in a new return folder. Owner import: <code>%s</code>. A candidate cannot choose or weaken the checker. Do not execute submitted code.</p>
<details>
<summary>Optional experiment conditions A and B</summary>
<ul>
%s
</ul>
</details>
<details>
<summary>Digests, assessments, and original evidence paths</summary>
<ul>
%s
%s
%s
%s
</ul>
</details>
<h2>Recipient prompt</h2>
<p><label for="recipient-prompt">Recipient prompt (selectable without JavaScript). The copy button is optional.</label></p>
<textarea id="recipient-prompt" readonly rows="24">%s</textarea>
<p><button type="button" id="copy-prompt">Copy recipient prompt</button></p>
<p id="copy-status" hidden></p>
<script>
(function () {
  var button = document.getElementById("copy-prompt");
  var status = document.getElementById("copy-status");
  var prompt = document.getElementById("recipient-prompt");
  function say(msg) { status.hidden = false; status.textContent = msg; }
  button.addEventListener("click", function () {
    var text = prompt.value;
    if (!navigator.clipboard || !navigator.clipboard.writeText) {
      say("Clipboard is unavailable. Select the prompt text above and copy it yourself.");
      return;
    }
    navigator.clipboard.writeText(text).then(function () {
      say("Copied.");
    }).catch(function () {
      say("Clipboard is unavailable. Select the prompt text above and copy it yourself.");
    });
  });
})();
</script>
</body>
</html>
''' % (esc(target['question']), esc(brief['current_assessment']),
       esc(brief['proposed_next_check']), html_links(primary_links(target, view)),
       esc(owner_tool(packaged) + ' submit RETURN_FOLDER/submission.json'),
       html_links(ab_links()),
       detail_rows,
       '\n'.join(attempts) or '<li>No prior attempts are in this export.</li>',
       '\n'.join(assessments) or '<li>No assessments are in this export.</li>',
       html_links(evidence), esc(prompt))


def render_md(target_key, target, brief, view, assignment, packaged=False):
    attempts = []
    for key, a in view['attempts'].items():
        path = 'C/history/attempt-' + key + '.json'
        attempts.append('- [%s](%s) (%s): %s'
                        % (md_safe(attempt_context(key, a)), href_path(path), md_safe(a['outcome']),
                           md_safe(a['observation'])))
    assessments = []
    for key, a in view['assessments'].items():
        path = 'C/history/assessment-' + key + '.json'
        assessments.append('- [%s](%s): %s'
                           % (md_safe(assessment_label(key, a, view['attempts'])), href_path(path),
                              md_safe(a['rationale'])))
    evidence = [item for item in local_links(target, view)
                if item not in primary_links(target, view) and item[1] not in {p for _, p in ab_links()}]
    prompt = recipient_prompt(target_key, target, brief, view, assignment, packaged)
    return '\n'.join([
        '# Local research starting page',
        '',
        'This is a static local folder. It cannot launch an agent, mutate the store, verify science, or enforce resource budgets. You do not need researchers or command-line tools to read the question, the observed result, and the next step.',
        '',
        '## The question',
        '',
        md_safe(target['question']),
        '',
        '## What was already checked',
        '',
        md_safe(brief['current_assessment']),
        '',
        '## One next action',
        '',
        md_safe(brief['proposed_next_check']),
        '',
        '## Open the local files',
        '',
        md_links(primary_links(target, view)),
        '',
        '## Use and return this folder',
        '',
        return_guide(assignment, packaged, target).replace('\n', '\n\n'),
        '',
        '<details>',
        '<summary>Optional experiment conditions A and B</summary>',
        '',
        md_links(ab_links()),
        '',
        '</details>',
        '',
        '## Digests, assessments, and original evidence paths',
        '',
        '- Owner: ' + md_safe(target['owner']),
        '- Scope: ' + md_safe(target['scope']),
        '- Assumptions: ' + md_safe(target['assumptions']),
        '- stop_condition: ' + md_safe(target['stop_condition']),
        '- Unresolved: ' + md_safe(brief['unresolved_checks']),
        '- Target digest: `' + target_key + '`',
        '- Base snapshot: `' + assignment['base_snapshot'] + '`',
        '- Resources: `' + json.dumps(assignment['resources'], ensure_ascii=False, sort_keys=True) + '`',
        '\n'.join(attempts) if attempts else '- No prior attempts are in this export.',
        '\n'.join(assessments) if assessments else '- No assessments are in this export.',
        md_links(evidence),
        '',
        '## Recipient prompt',
        '',
        'Select and copy the following text. This file does not launch an agent.',
        '',
        fence(prompt),
    ]) + '\n'


def build(destination, store=None, target=None, brief=None, packaged=False):
    destination = Path(destination)
    if brief is None and (not is_default_store(store) or not is_default_target(target)):
        raise ValueError('custom store or target requires an explicit matching brief')
    if brief is None:
        brief = h.read_json(MVP_BRIEF)
    h.require(not destination.exists(), 'output folder already exists; refusing to overwrite')
    store = Path(store) if store is not None else DEFAULT_STORE
    target_key = resolve_target(store, target)
    destination.mkdir(parents=True)
    assignment = None
    for arm in 'ABCD':
        assignment = h.export(store, target_key, destination / arm, arm, brief)
    view = h.inspect_target(store, target_key)
    target_obj = view['targets'][target_key]
    h.create_file(destination / 'index.html',
                  render_html(target_key, target_obj, brief, view, assignment, packaged).encode('utf-8'))
    h.create_file(destination / 'START.md',
                  render_md(target_key, target_obj, brief, view, assignment, packaged).encode('utf-8'))
    h.create_file(destination / 'submission-template.json',
                  h.encoded(submission_template(target_key, target_obj, assignment)))
    h.create_file(destination / 'USE.md',
                  use_md(assignment, packaged, target_obj).encode('utf-8'))
    return destination


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('destination', type=Path)
    p.add_argument('--store', type=Path, default=None)
    p.add_argument('--target')
    p.add_argument('--brief', type=Path, default=None)
    args = p.parse_args(argv)
    try:
        brief = h.read_json(args.brief) if args.brief is not None else None
        build(args.destination, args.store, args.target, brief)
    except (ValueError, KeyError, OSError) as error:
        p.exit(1, 'Cannot complete: ' + str(error) + '\n')


if __name__ == '__main__':
    main()
