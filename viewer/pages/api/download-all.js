import path from 'path';
import fs from 'fs';
import archiver from 'archiver';
import { RESULTS_ROOT } from '../../lib/serverPaths';
import { getPngPath } from '../../renderer/index.js';

function safe(s) {
  return s && typeof s === 'string' && !s.includes('..') && !s.includes('\\') && s.length < 512;
}

function walkFiles(dir, exts, out = []) {
  for (const e of fs.readdirSync(dir, { withFileTypes: true })) {
    const p = path.join(dir, e.name);
    if (e.isDirectory()) {
      if (e.name === '.git' || e.name === 'node_modules' || e.name.startsWith('.next')) continue;
      walkFiles(p, exts, out);
    } else if (e.isFile()) {
      const ext = path.extname(e.name).toLowerCase();
      if (exts.includes(ext)) out.push(p);
    }
  }
  return out;
}

export default async function handler(req, res) {
  if (req.method !== 'GET') {
    res.status(405).json({ error: 'Method not allowed' });
    return;
  }

  const { run } = req.query;

  if (!safe(run)) {
    res.status(400).json({ error: 'invalid args' });
    return;
  }

  const runDir = path.join(RESULTS_ROOT, run);

  if (!fs.existsSync(runDir)) {
    res.status(404).json({ error: 'run not found' });
    return;
  }

  const imageDirs = fs.readdirSync(runDir, { withFileTypes: true })
    .filter(d => d.isDirectory())
    .map(d => ({ name: d.name, path: path.join(runDir, d.name) }));

  let totalFiles = 0;
  let totalWithPng = 0;

  for (const imageDir of imageDirs) {
    const targets = walkFiles(imageDir.path, ['.html', '.jsx', '.js']);

    for (const f of targets) {
      const png = getPngPath(f);
      if (fs.existsSync(png)) {
        totalWithPng++;
      }
    }

    totalFiles += targets.length;
  }

  const complete = totalFiles > 0 ? totalFiles === totalWithPng : false;
  const missingCount = totalFiles - totalWithPng;

  if (!complete) {
    console.log(`[download-all] Rejected: ${run} is incomplete (${missingCount}/${totalFiles} PNGs missing)`);
    res.status(400).json({
      error: 'Incomplete run',
      message: `Cannot download: ${missingCount} of ${totalFiles} PNGs are not rendered yet`,
      complete: false,
      total: totalFiles,
      missing: missingCount
    });
    return;
  }

  try {
    const archive = archiver('zip', {
      zlib: { level: 6 }
    });

    res.setHeader('Content-Type', 'application/zip');
    res.setHeader('Content-Disposition', `attachment; filename="${run}.zip"`);

    archive.on('error', (err) => {
      console.error('Archive error:', err);
      res.status(500).end();
    });

    archive.pipe(res);

    const imageDirs = fs.readdirSync(runDir, { withFileTypes: true })
      .filter(d => d.isDirectory())
      .map(d => d.name);

    let fileCount = 0;

    function addDirectory(dirPath, archivePrefix) {
      const items = fs.readdirSync(dirPath, { withFileTypes: true });

      for (const item of items) {
        const itemPath = path.join(dirPath, item.name);
        const archivePath = path.join(archivePrefix, item.name);

        if (item.isDirectory()) {
          addDirectory(itemPath, archivePath);
        } else if (item.isFile()) {
          archive.file(itemPath, { name: archivePath });
          fileCount++;
        }
      }
    }

    for (const imageDir of imageDirs) {
      const imagePath = path.join(runDir, imageDir);
      addDirectory(imagePath, imageDir);
    }

    if (fileCount === 0) {
      archive.append('No files found', { name: 'README.txt' });
    }

    console.log(`[download-all] Archiving ${fileCount} files for run "${run}"`);

    await archive.finalize();
  } catch (err) {
    console.error('Download all error:', err);
    if (!res.headersSent) {
      res.status(500).json({ error: String(err.message || err) });
    }
  }
}
