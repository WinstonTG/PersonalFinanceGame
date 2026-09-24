// Publish only student-facing assets, never instructor code, databases or tests.
import {mkdir, copyFile, readdir} from 'node:fs/promises';
import {fileURLToPath} from 'node:url';

const root = new URL('../', import.meta.url);
const output = new URL('dist/', root);
export const publicFiles = [
  'index.html', 'styles.css', 'app.js', 'simulation.js',
  'budget.html', 'budget.css', 'budget.js', 'budget-model.js', 'deployment.json',
];
await mkdir(output, {recursive:true});
// Refuse to publish unexpected leftovers rather than accidentally exposing them.
for (const name of await readdir(output)) {
  if (!publicFiles.includes(name)) throw Error(`Unexpected file in dist: ${name}. Review it before deploying.`);
}
await Promise.all(publicFiles.map(name=>copyFile(new URL('web/'+name,root),new URL(name,output))));
console.log(`Built ${publicFiles.length} student assets in ${fileURLToPath(output)}`);
