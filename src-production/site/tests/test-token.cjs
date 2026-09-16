// Canario do token no frontend: fragmento -> sessionStorage -> header, nunca em query string.

const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

const fonte = fs.readFileSync(path.join(__dirname, '..', 'js', 'api.js'), 'utf8');

function carrega(hash) {
  const trocas = [];
  const guardados = new Map();
  const janela = {
    location: {
      origin: 'http://localhost',
      pathname: '/',
      search: '?aba=capturas',
      hash
    },
    sessionStorage: {
      setItem: (k, v) => guardados.set(k, v),
      getItem: k => (guardados.has(k) ? guardados.get(k) : null)
    }
  };
  const contexto = {
    window: janela,
    history: { replaceState: (a, b, url) => trocas.push(url) },
    AbortSignal: { timeout: () => ({}) },
    URL,
    fetch: async () => {
      throw new Error('not used');
    }
  };
  vm.runInNewContext(fonte, contexto, { filename: 'api.js' });
  return { janela, trocas, guardados };
}

// 1. fragmento vira header, guarda em sessionStorage e sai da barra de endereco
const comToken = carrega('#token=segredo123');
assert.equal(comToken.guardados.get('pnaat_token'), 'segredo123', 'token deve ir para sessionStorage');
assert.equal(
  comToken.janela.PNAAT_HEADERS().Authorization,
  'Bearer segredo123',
  'header de POST deve carregar o bearer'
);
assert.deepEqual(comToken.trocas, ['/?aba=capturas'], 'URL limpa preserva a query e descarta o fragmento');

// 2. sem fragmento e sem sessao nao existe header de autorizacao
const semToken = carrega('');
assert.equal(semToken.janela.PNAAT_HEADERS().Authorization, undefined);
assert.equal(semToken.guardados.size, 0);
assert.equal(semToken.trocas.length, 0);

// 3. headers extras sobrevivem ao merge
const extras = comToken.janela.PNAAT_HEADERS({ 'Content-Type': 'application/json' });
assert.equal(extras['Content-Type'], 'application/json');
assert.equal(extras.Authorization, 'Bearer segredo123');

// 4. o token nunca e montado em query string: fora de comentario, token= so aparece na
// leitura do fragmento
const codigo = fonte
  .split('\n')
  .filter(linha => !/^\s*(\/\/|\*|\/\*)/.test(linha))
  .join('\n');
const mencoes = codigo.split('token=').length - 1;
assert.equal(mencoes, 1, `token= fora de comentario deve ser so a leitura do fragmento (achei ${mencoes})`);

console.log('PASS contrato de token do frontend (fragmento -> sessionStorage -> header)');
