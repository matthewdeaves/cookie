#!/usr/bin/env node
/**
 * Generate frontend complexity report using escomplex.
 *
 * Analyzes TypeScript/JavaScript files for cyclomatic complexity and
 * generates summary JSON and HTML report for the metrics dashboard.
 *
 * Usage:
 *   node generate-frontend-complexity-report.js
 */

const fs = require('fs');
const path = require('path');

// Try to use typhonjs-escomplex for better TS support
// Modules are installed in the current working directory (frontend/)
let escomplex;
try {
  escomplex = require(path.join(process.cwd(), 'node_modules', 'typhonjs-escomplex'));
} catch (e) {
  try {
    escomplex = require(path.join(process.cwd(), 'node_modules', 'escomplex'));
  } catch (e2) {
    // Fall back to global require if neither works
    try {
      escomplex = require('typhonjs-escomplex');
    } catch (e3) {
      escomplex = require('escomplex');
    }
  }
}

function walkDir(dir, files = []) {
  const entries = fs.readdirSync(dir, { withFileTypes: true });
  for (const entry of entries) {
    const fullPath = path.join(dir, entry.name);
    if (entry.isDirectory() && !entry.name.includes('node_modules') && !entry.name.includes('test')) {
      walkDir(fullPath, files);
    } else if (entry.isFile() && /\.(ts|tsx|js|jsx)$/.test(entry.name) && !entry.name.includes('.test.')) {
      files.push(fullPath);
    }
  }
  return files;
}

const files = walkDir('src');
let totalCC = 0;
let functionCount = 0;
let maxCC = 0;
let highComplexityFunctions = [];
const fileMetrics = [];

for (const file of files) {
  try {
    let code = fs.readFileSync(file, 'utf8');

    // Strip TypeScript-specific syntax for escomplex compatibility
    code = code
      .replace(/:\s*[A-Za-z<>\[\]|&\s,{}()=>?."']+(?=[,\)\s=;{])/g, '')  // Type annotations
      .replace(/\binterface\s+\w+[^{]*\{[^}]*\}/g, '')  // Interfaces
      .replace(/\btype\s+\w+[^=]*=[^;]+;/g, '')  // Type aliases
      .replace(/<[A-Za-z,\s]+>/g, '')  // Generics
      .replace(/\bas\s+\w+/g, '')  // Type assertions
      .replace(/\bexport\s+type\b/g, 'export')  // Export type
      .replace(/\bimport\s+type\b/g, 'import');  // Import type

    const result = escomplex.analyse(code, { sourceType: 'module' });

    let fileCC = 0;
    let fileFunctions = 0;

    if (result.methods) {
      for (const method of result.methods) {
        const cc = method.cyclomatic || 1;
        totalCC += cc;
        functionCount++;
        fileCC += cc;
        fileFunctions++;

        if (cc > maxCC) maxCC = cc;
        if (cc > 10) {
          highComplexityFunctions.push({
            file: file.replace('src/', ''),
            name: method.name,
            complexity: cc
          });
        }
      }
    }

    if (fileFunctions > 0) {
      fileMetrics.push({
        file: file.replace('src/', ''),
        avgCC: Math.round(fileCC / fileFunctions * 100) / 100,
        functions: fileFunctions
      });
    }
  } catch (e) {
    // Skip files that can't be parsed (complex TS, JSX edge cases)
  }
}

const avgCC = functionCount > 0 ? Math.round(totalCC / functionCount * 100) / 100 : 0;

// Read ESLint warnings for backwards compatibility
let eslintReport = [];
let complexityWarnings = 0;
try {
  eslintReport = JSON.parse(fs.readFileSync('complexity/eslint-report.json', 'utf8'));
  eslintReport.forEach(file => {
    file.messages.forEach(msg => {
      if (msg.ruleId === 'complexity') complexityWarnings++;
    });
  });
} catch (e) {}

// Rating based on average CC (same thresholds as backend)
// A: <= 5, B: <= 10, C: <= 20, D: > 20
let rating;
if (avgCC <= 5) rating = 'A';
else if (avgCC <= 10) rating = 'B';
else if (avgCC <= 20) rating = 'C';
else rating = 'D';

const summary = {
  avg_cyclomatic_complexity: avgCC,
  max_cyclomatic_complexity: maxCC,
  total_functions_analyzed: functionCount,
  total_files_analyzed: files.length,
  high_complexity_functions: highComplexityFunctions.length,
  complexity_warnings: complexityWarnings,
  rating: rating
};

// Ensure complexity directory exists
fs.mkdirSync('complexity', { recursive: true });

// Save detailed metrics
fs.writeFileSync('complexity/file-metrics.json', JSON.stringify(fileMetrics.sort((a, b) => b.avgCC - a.avgCC), null, 2));
fs.writeFileSync('complexity/high-complexity.json', JSON.stringify(highComplexityFunctions.sort((a, b) => b.complexity - a.complexity), null, 2));
fs.writeFileSync('complexity/summary.json', JSON.stringify(summary, null, 2));

// Generate HTML report
const sortedFiles = fileMetrics.sort((a, b) => b.avgCC - a.avgCC);
const sortedHighCC = highComplexityFunctions.sort((a, b) => b.complexity - a.complexity);

const ratingColors = { A: '#4c1', B: '#97ca00', C: '#dfb317', D: '#e05d44' };
const ratingColor = ratingColors[rating] || '#9f9f9f';

let highCCSection = '';
if (sortedHighCC.length > 0) {
  const rows = sortedHighCC.map(f =>
    `<tr><td><code>${f.name}</code></td><td>${f.file}</td><td class="cc-high">${f.complexity}</td></tr>`
  ).join('\n                ');

  highCCSection = `
            <h2>High Complexity Functions (CC &gt; 10)</h2>
            <table>
              <thead><tr><th>Function</th><th>File</th><th>Complexity</th></tr></thead>
              <tbody>
                ${rows}
              </tbody>
            </table>`;
} else {
  highCCSection = '<p style="color:#4c1;margin:1rem 0;">&check; No functions with complexity &gt; 10</p>';
}

const fileRows = sortedFiles.slice(0, 50).map(f => {
  const ccClass = f.avgCC > 10 ? 'cc-high' : f.avgCC > 5 ? 'cc-medium' : 'cc-low';
  return `<tr><td>${f.file}</td><td class="${ccClass}">${f.avgCC}</td><td>${f.functions}</td></tr>`;
}).join('\n                ');

const html = `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Frontend Complexity Report</title>
  <style>
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width: 1200px; margin: 0 auto; padding: 2rem; background: #f5f5f5; color: #333; }
    h1 { font-size: 2rem; margin-bottom: 0.5rem; }
    .subtitle { color: #666; margin-bottom: 2rem; }
    h2 { font-size: 1.25rem; margin: 2rem 0 1rem; border-bottom: 2px solid #e1e4e8; padding-bottom: 0.5rem; }
    .summary { display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 1rem; margin-bottom: 2rem; }
    .stat { background: white; padding: 1rem; border-radius: 8px; text-align: center; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
    .stat-value { font-size: 2rem; font-weight: bold; }
    .stat-label { color: #666; font-size: 0.85rem; }
    .rating { display: inline-block; padding: 0.25rem 0.75rem; border-radius: 4px; color: white; font-weight: bold; }
    table { width: 100%; border-collapse: collapse; background: white; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 4px rgba(0,0,0,0.1); margin-bottom: 2rem; }
    th, td { padding: 0.75rem 1rem; text-align: left; border-bottom: 1px solid #e1e4e8; }
    th { background: #f6f8fa; font-weight: 600; }
    tr:hover { background: #f6f8fa; }
    .cc-high { color: #e05d44; font-weight: bold; }
    .cc-medium { color: #dfb317; }
    .cc-low { color: #4c1; }
    .back-link { display: inline-block; margin-bottom: 1rem; color: #0066cc; text-decoration: none; }
    .back-link:hover { text-decoration: underline; }
    code { background: #f3f4f6; padding: 0.1rem 0.3rem; border-radius: 3px; font-size: 0.9rem; }
  </style>
</head>
<body>
  <a href="../index.html" class="back-link">&larr; Back to Dashboard</a>
  <h1>Frontend Complexity Report</h1>
  <p class="subtitle">Cyclomatic complexity analysis for React/TypeScript code</p>

  <div class="summary">
    <div class="stat">
      <div class="stat-value">${avgCC}</div>
      <div class="stat-label">Avg. Complexity</div>
    </div>
    <div class="stat">
      <div class="stat-value">${maxCC}</div>
      <div class="stat-label">Max Complexity</div>
    </div>
    <div class="stat">
      <div class="stat-value">${functionCount}</div>
      <div class="stat-label">Functions</div>
    </div>
    <div class="stat">
      <div class="stat-value">${files.length}</div>
      <div class="stat-label">Files</div>
    </div>
    <div class="stat">
      <div class="stat-value"><span class="rating" style="background:${ratingColor}">${rating}</span></div>
      <div class="stat-label">Rating</div>
    </div>
  </div>

  ${highCCSection}

  <h2>File Complexity (sorted by avg. CC)</h2>
  <table>
    <thead><tr><th>File</th><th>Avg. CC</th><th>Functions</th></tr></thead>
    <tbody>
      ${fileRows}
    </tbody>
  </table>

  <p style="color:#666;font-size:0.85rem;margin-top:2rem;">
    Generated: ${new Date().toISOString()}<br>
    Rating thresholds: A &le; 5, B &le; 10, C &le; 20, D &gt; 20
  </p>
</body>
</html>`;

fs.writeFileSync('complexity/frontend-complexity.html', html);

console.log('Frontend complexity:', JSON.stringify(summary, null, 2));
console.log(`\nAverage Cyclomatic Complexity: ${avgCC} (${rating})`);
console.log(`Functions analyzed: ${functionCount}`);
console.log(`High complexity functions (CC > 10): ${highComplexityFunctions.length}`);
