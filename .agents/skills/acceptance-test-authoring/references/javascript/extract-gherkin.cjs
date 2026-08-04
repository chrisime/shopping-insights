'use strict';

// Extracts classic Gherkin from Markdown specs (spec.md) into .feature files.
//
// A spec.md holds prose plus Gherkin inside column-0 ```gherkin fences. The
// extraction copies every line inside a gherkin fence VERBATIM at its
// original position and turns every other line (prose, fence markers, bodies
// of non-gherkin fences) into an empty line. The output therefore has the
// IDENTICAL line count to the input: line N of the extracted .feature is
// line N of the spec.md. gherkin-lint messages, cucumber failure locations
// and effective-spec line targeting (`spec.feature:27:33`) all point at valid
// spec.md lines with no translation. NEVER "improve" this to collapse blank
// lines — that invariant is what the whole toolchain leans on.
//
// Fences follow CommonMark: an opener is 3+ backticks at column 0 with info
// string exactly `gherkin`; the closer is at least as many backticks at
// column 0. Non-gherkin fences are tracked too, so a ```gherkin quoted
// inside a longer documentation fence cannot false-trigger. Gherkin
// docstrings delimited by ``` are safe: they are always indented, and the
// closer regex requires column 0.
//
// Failure modes are loud, never silent: an unclosed fence, a spec.md with no
// gherkin fence, or an INDENTED ```gherkin opener (which would otherwise
// silently drop its scenarios from the suite) are hard errors.

// Deliberately dependency-free (node:fs/node:path only): the CLI form must
// run from the skill's references/ directory, where no node_modules exists.

const fs = require('node:fs');
const path = require('node:path');

const GHERKIN_OPEN_RE = /^(`{3,})gherkin\s*$/;
const ANY_OPEN_RE = /^(`{3,})\S*\s*$/;
const INDENTED_GHERKIN_RE = /^\s+`{3,}gherkin\s*$/;

function extractFile(mdPath) {
  const lines = fs.readFileSync(mdPath, 'utf8').split(/\r?\n/);
  const out = [];
  let state = 'prose'; // 'prose' | 'gherkin' | 'other-fence'
  let fenceTicks = 0;
  let openLine = 0;
  let gherkinFences = 0;

  lines.forEach((line, i) => {
    if (state === 'prose') {
      let m;
      if ((m = GHERKIN_OPEN_RE.exec(line))) {
        state = 'gherkin';
        fenceTicks = m[1].length;
        openLine = i + 1;
        gherkinFences += 1;
        out.push('');
      } else if (INDENTED_GHERKIN_RE.test(line)) {
        throw new Error(
          `${mdPath}:${i + 1}: indented \`\`\`gherkin fence — gherkin fences must start at column 0`
        );
      } else if ((m = ANY_OPEN_RE.exec(line))) {
        state = 'other-fence';
        fenceTicks = m[1].length;
        openLine = i + 1;
        out.push('');
      } else {
        out.push('');
      }
      return;
    }
    const close = new RegExp('^`{' + fenceTicks + ',}\\s*$');
    if (close.test(line)) {
      state = 'prose';
      out.push('');
    } else {
      out.push(state === 'gherkin' ? line : '');
    }
  });

  if (state !== 'prose') {
    throw new Error(`${mdPath}:${openLine}: unclosed fence`);
  }
  if (gherkinFences === 0) {
    throw new Error(`${mdPath}: no \`\`\`gherkin fences found — a spec.md must contain gherkin`);
  }
  if (out.length !== lines.length) {
    throw new Error(`${mdPath}: line-count invariant violated (extractor bug)`);
  }
  return out.join('\n');
}

// Recursively collects files named <basename> under <dir>, returned as
// posix paths relative to <root>, sorted for deterministic output.
function walk(root, dir, basename, found) {
  if (!fs.existsSync(dir)) return found;
  for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
    const abs = path.join(dir, entry.name);
    if (entry.isDirectory()) walk(root, abs, basename, found);
    else if (entry.name === basename || (basename.startsWith('*.') && entry.name.endsWith(basename.slice(1)))) {
      found.push(path.relative(root, abs).split(path.sep).join('/'));
    }
  }
  return found;
}

// Spec roots: specs/ (source of truth) and each active change's specs/ —
// changes/archive/ is excluded structurally (archive nests one level deeper
// than changes/<id>/) plus a defensive filter on the collected paths.
function collectSpecSources(openspecDir, basename) {
  const found = walk(openspecDir, path.join(openspecDir, 'specs'), basename, []);
  const changesDir = path.join(openspecDir, 'changes');
  if (fs.existsSync(changesDir)) {
    for (const entry of fs.readdirSync(changesDir, { withFileTypes: true })) {
      if (!entry.isDirectory() || entry.name === 'archive') continue;
      walk(openspecDir, path.join(changesDir, entry.name, 'specs'), basename, found);
    }
  }
  return found.filter((p) => !p.includes('changes/archive/')).sort();
}

// Extracts every spec.md under <openspecDir> (source of truth + active
// change deltas, archive excluded) into <outDir>, mirroring the
// openspec-relative path with spec.md -> spec.feature. The output dir is
// wiped first — a stale extraction would keep deleted or renamed
// capabilities executing.
function extractAll(openspecDir, outDir) {
  openspecDir = openspecDir ? path.resolve(openspecDir) : path.resolve(__dirname, '../openspec');
  outDir = outDir ? path.resolve(outDir) : path.resolve(__dirname, '.extracted');

  fs.rmSync(outDir, { recursive: true, force: true });

  const sources = collectSpecSources(openspecDir, 'spec.md');

  // Legacy-format tripwire: raw .feature files under openspec/ no longer run
  // anywhere — flag them instead of letting them silently drop out.
  const legacy = collectSpecSources(openspecDir, '*.feature');
  if (legacy.length > 0) {
    console.error(
      `[extract-gherkin] WARNING: legacy .feature file(s) under openspec/ are ignored ` +
        `(specs are spec.md now): ${legacy.join(', ')}`
    );
  }

  const written = [];
  for (const rel of sources) {
    const dest = path.join(outDir, rel.replace(/spec\.md$/, 'spec.feature'));
    fs.mkdirSync(path.dirname(dest), { recursive: true });
    fs.writeFileSync(dest, extractFile(path.join(openspecDir, rel)));
    written.push(dest);
  }
  return { outDir, written };
}

module.exports = { extractAll, extractFile };

// CLI: node extract-gherkin.cjs [openspecDir] [outDir]
if (require.main === module) {
  try {
    const { outDir, written } = extractAll(process.argv[2], process.argv[3]);
    console.error(`[extract-gherkin] ${written.length} spec.md file(s) extracted to ${outDir}`);
  } catch (err) {
    console.error(`[extract-gherkin] ${err.message}`);
    process.exit(1);
  }
}
