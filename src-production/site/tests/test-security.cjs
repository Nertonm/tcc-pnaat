const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

const source = fs.readFileSync(path.join(__dirname, '..', 'js', 'api.js'), 'utf8');
const context = {
    window: { location: { origin: 'http://localhost' } },
    AbortSignal: { timeout: () => ({}) },
    URL,
    fetch: async () => { throw new Error('not used'); }
};
vm.runInNewContext(source, context, { filename: 'api.js' });

assert.equal(
    typeof context.window.PNAAT_ESCAPE,
    'function',
    'api.js deve expor o escape HTML comum'
);
assert.equal(
    context.window.PNAAT_ESCAPE('<img src=x onerror=alert(1)>'),
    '&lt;img src=x onerror=alert(1)&gt;'
);
assert.equal(context.window.PNAAT_ESCAPE('a & b "c"'), 'a &amp; b &quot;c&quot;');
console.log('PASS frontend escape contract');

assert.equal(context.window.PNAAT_SAFE_URL('javascript:alert(1)'), '');
assert.equal(context.window.PNAAT_SAFE_URL('https://evil.example/x'), '');
assert.equal(context.window.PNAAT_SAFE_URL('/api/evidencia?item=x'), '/api/evidencia?item=x');

assert.equal(context.window.PNAAT_OPERATION_OK({ ok: true, dados: { confirmado: true } }), true);
assert.equal(context.window.PNAAT_OPERATION_OK({ ok: true, dados: { parcial: true } }), false);
assert.equal(context.window.PNAAT_OPERATION_OK({ ok: true, dados: { rig: { ok: false } } }), false);
assert.equal(context.window.PNAAT_OPERATION_OK({ ok: true, dados: { confirmado: false } }), false);
