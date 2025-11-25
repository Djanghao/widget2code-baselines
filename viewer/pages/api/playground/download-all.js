import path from 'path';
import fs from 'fs';
import archiver from 'archiver';
import { TMP_PLAYGROUND_ROOT } from '../../../lib/serverPaths';

function walkFiles(dir, out = []) {
  if (!fs.existsSync(dir)) return out;
  for (const e of fs.readdirSync(dir, { withFileTypes: true })) {
    const p = path.join(dir, e.name);
    if (e.isDirectory()) {
      if (e.name === '.git' || e.name === 'node_modules' || e.name.startsWith('.next')) continue;
      walkFiles(p, out);
    } else if (e.isFile()) {
      out.push(p);
    }
  }
  return out;
}

export default async function handler(req, res) {
  if (req.method !== 'GET') {
    res.status(405).json({ error: 'Method not allowed' });
    return;
  }

  const playgroundDir = TMP_PLAYGROUND_ROOT;

  if (!fs.existsSync(playgroundDir)) {
    res.status(404).json({ error: 'playground directory not found' });
    return;
  }

  try {
    const archive = archiver('zip', {
      zlib: { level: 6 }
    });

    const timestamp = new Date().toISOString().replace(/[:.]/g, '-').slice(0, -5);
    const filename = `playground-${timestamp}.zip`;

    res.setHeader('Content-Type', 'application/zip');
    res.setHeader('Content-Disposition', `attachment; filename="${filename}"`);

    archive.on('error', (err) => {
      console.error('Archive error:', err);
      res.status(500).end();
    });

    archive.pipe(res);

    let fileCount = 0;

    function addDirectory(dirPath, archivePrefix) {
      const items = fs.readdirSync(dirPath, { withFileTypes: true });

      for (const item of items) {
        const itemPath = path.join(dirPath, item.name);
        const archivePath = archivePrefix ? path.join(archivePrefix, item.name) : item.name;

        if (item.isDirectory()) {
          if (item.name === '.git' || item.name === 'node_modules' || item.name.startsWith('.next')) {
            continue;
          }
          addDirectory(itemPath, archivePath);
        } else if (item.isFile()) {
          archive.file(itemPath, { name: archivePath });
          fileCount++;
        }
      }
    }

    addDirectory(playgroundDir, '');

    if (fileCount === 0) {
      archive.append('No files found in playground', { name: 'README.txt' });
    }

    console.log(`[playground/download-all] Archiving ${fileCount} files from playground`);

    await archive.finalize();
  } catch (err) {
    console.error('Playground download all error:', err);
    if (!res.headersSent) {
      res.status(500).json({ error: String(err.message || err) });
    }
  }
}
