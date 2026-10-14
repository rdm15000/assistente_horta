// Roadmap interativo: clicar num ponto abre o painel com a explicação
// validada e o campo para pedir ajuda da IA sobre aquele ponto.

const overlay = document.getElementById("overlay");
const painel = document.getElementById("painel");
const fechar = document.getElementById("fechar-painel");

const elEtapa = document.getElementById("painel-etapa");
const elTitulo = document.getElementById("painel-titulo");
const elConteudo = document.getElementById("painel-conteudo");

const formIA = document.getElementById("form-ia");
const perguntaIA = document.getElementById("pergunta-ia");
const btnIA = document.getElementById("btn-ia");
const iaStatus = document.getElementById("ia-status");
const iaRespostas = document.getElementById("ia-respostas");

let pontoAtual = null; // { etapa_idx, item_idx } — índices absolutos, usados pela API

// Localiza o ponto pelo id ("e1-p0"). Os índices guardados em cada item são
// absolutos (contam a etapa de variedades), mas a árvore exibida começa na
// etapa seguinte — por isso a busca é por id, e não por posição.
function acharPonto(id) {
  for (let pos = 0; pos < window.ROADMAP.length; pos++) {
    const etapa = window.ROADMAP[pos];
    const item = etapa.itens.find((i) => i.id === id);
    if (item) return { etapa, item, pos };
  }
  return null;
}

function abrirPainel(id) {
  const achado = acharPonto(id);
  if (!achado) return;
  const { etapa, item, pos } = achado;
  pontoAtual = { etapa_idx: item.etapa_idx, item_idx: item.item_idx };

  elEtapa.textContent = `Etapa ${pos + 1} · ${etapa.titulo} · ${window.TIPO_NOME}`;
  elTitulo.textContent = item.titulo;
  elConteudo.textContent = item.conteudo || "(sem conteúdo cadastrado ainda para este ponto)";

  iaRespostas.innerHTML = "";
  perguntaIA.value = "";
  iaStatus.hidden = true;

  document.querySelectorAll(".no-ponto.ativo").forEach((b) => b.classList.remove("ativo"));
  document.querySelector(`.no-ponto[data-id="${item.id}"]`)?.classList.add("ativo");

  overlay.hidden = false;
  painel.hidden = false;
  painel.scrollTop = 0;
  document.body.classList.add("painel-aberto");
}

function fecharPainel() {
  overlay.hidden = true;
  painel.hidden = true;
  document.body.classList.remove("painel-aberto");
  document.querySelectorAll(".no-ponto.ativo").forEach((b) => b.classList.remove("ativo"));
}

document.querySelectorAll(".no-ponto").forEach((btn) => {
  btn.addEventListener("click", () => abrirPainel(btn.dataset.id));
});

fechar.addEventListener("click", fecharPainel);
overlay.addEventListener("click", fecharPainel);
document.addEventListener("keydown", (e) => {
  if (e.key === "Escape" && !painel.hidden) fecharPainel();
});

// Sugestões de pergunta: preenchem o campo e já enviam.
document.querySelectorAll(".sugestao").forEach((s) => {
  s.addEventListener("click", () => {
    perguntaIA.value = s.textContent;
    formIA.requestSubmit();
  });
});

function addResposta(pergunta, resposta) {
  const wrap = document.createElement("div");
  wrap.className = "resposta";

  const p = document.createElement("p");
  p.className = "resposta-pergunta";
  p.textContent = pergunta;

  const r = document.createElement("div");
  r.className = "resposta-texto";
  r.textContent = resposta;

  wrap.appendChild(p);
  wrap.appendChild(r);
  iaRespostas.appendChild(wrap);
  wrap.scrollIntoView({ behavior: "smooth", block: "nearest" });
}

formIA.addEventListener("submit", async (e) => {
  e.preventDefault();
  if (!pontoAtual) return;
  const pergunta = perguntaIA.value.trim();
  if (!pergunta) return;

  btnIA.disabled = true;
  perguntaIA.disabled = true;
  iaStatus.hidden = false;

  try {
    const resp = await fetch("/api/ajuda", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        hortalica: window.HORTALICA,
        tipo: window.TIPO,
        etapa_idx: pontoAtual.etapa_idx,
        item_idx: pontoAtual.item_idx,
        pergunta,
      }),
    });
    const data = await resp.json();
    addResposta(pergunta, data.erro ? `Erro: ${data.erro}` : data.resposta);
    perguntaIA.value = "";
  } catch (err) {
    addResposta(pergunta, "Não consegui falar com o servidor. Tenta de novo.");
  } finally {
    btnIA.disabled = false;
    perguntaIA.disabled = false;
    iaStatus.hidden = true;
    perguntaIA.focus();
  }
});
