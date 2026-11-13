"""Gera as páginas de busca do site (uma por ramo, a de IA e a de Teresina),
o sitemap.xml e o llms.txt.

Fonte única dos recursos de cada ramo: os <article class="ramo"> do index.html.
Este script só acrescenta o texto de abertura e as perguntas de cada página;
o que o Zaq faz em cada ramo continua sendo escrito num lugar só, na home.

Uso (na raiz do repositório):
    python3 ferramentas/gerar_paginas_seo.py

Regra do conteúdo: nada aqui pode prometer o que a home não diz. Número só com
data (o da home é de 29/10/2026); nome de cliente, nunca.
"""

from __future__ import annotations

import html
import json
import re
from datetime import date
from pathlib import Path
from urllib.parse import quote

RAIZ = Path(__file__).resolve().parent.parent
SITE = "https://zaq-ia.com"
WHATS = "5586981885930"
HOJE = date.today().isoformat()

# ---------------------------------------------------------------------------
# Conteúdo próprio de cada página. Os recursos (lista e tela) vêm da home.
# ---------------------------------------------------------------------------
RAMOS = [
    {
        "id": "clinica",
        "slug": "sistema-para-clinica",
        "nome": "Clínica",
        "titulo": "Sistema para clínica com IA no WhatsApp | Zaq",
        "h1": "Sistema para clínica, com IA no WhatsApp",
        "descricao": "Agendamento por link, lembrete no WhatsApp, fila e chamada na TV, prontuário, orçamento de pacotes, caixa e repasse por profissional. Para estética, odonto, fisioterapia e consultório.",
        "abertura": "O paciente marca pelo link e recebe o lembrete no WhatsApp; a IA atende quem chega pelo anúncio enquanto a recepção cuida da sala de espera e o profissional trabalha com fila e prontuário.",
        "msg": "Oi! Tenho uma clínica e quero um orçamento do Zaq",
        "perguntas": [
            ("O paciente consegue marcar sozinho?", "Consegue. O link de agendamento mostra os horários livres; o paciente confirma, remarca ou cancela sozinho, e o lembrete sai no WhatsApp."),
            ("O Zaq tem prontuário?", "Tem: prontuário com evolução assinada, fotos e documentos, ao lado da fila de atendimento do profissional."),
        ],
    },
    {
        "id": "hospital",
        "slug": "sistema-para-hospital",
        "nome": "Hospital",
        "titulo": "Sistema para hospital e centro de diagnóstico com IA | Zaq",
        "h1": "Sistema para hospital, com a palavra e o caminho do hospital",
        "descricao": "Para hospital-dia, centro de diagnóstico, maternidade e pronto atendimento: consultas, exames, cirurgias e procedimentos separados, funil próprio, chamada na TV com voz, prontuário e caixa.",
        "abertura": "Hospital-dia, centro de diagnóstico, maternidade e pronto atendimento usam as mesmas telas da clínica, mas com consultas, exames, cirurgias e procedimentos separados, funil próprio e chamada na TV da recepção com voz.",
        "msg": "Oi! Falo por um hospital e quero um orçamento do Zaq",
        "perguntas": [
            ("Separa consulta, exame e cirurgia?", "Separa. Consultas, exames, testes, cirurgias e procedimentos ficam no catálogo e nos relatórios, cada grupo com o seu número."),
            ("Como fica o paciente que faltou?", "O funil do hospital tem a etapa “faltou e não remarcou” e a mensagem de voltar a chamar."),
        ],
    },
    {
        "id": "eventos",
        "slug": "sistema-para-buffet-e-eventos",
        "nome": "Eventos e festas",
        "titulo": "Sistema para buffet e espaço de festas com IA no WhatsApp | Zaq",
        "h1": "Sistema para buffet e eventos, do primeiro oi ao pós-festa",
        "descricao": "Para buffet, espaço de festas, cerimonial e decoração: a data e os convidados lidos na conversa do WhatsApp, aviso de data ocupada, proposta por link, contrato e sinal via Pix.",
        "abertura": "Buffet, espaço de festas, cerimonial e decoração: o Zaq lê a data, o tipo e os convidados na própria conversa do WhatsApp, avisa quando duas festas caem no mesmo dia e leva o lead da visita ao contrato com sinal via Pix.",
        "msg": "Oi! Trabalho com eventos e quero um orçamento do Zaq",
        "perguntas": [
            ("O sistema avisa data ocupada?", "Avisa. O card lê a data na conversa e avisa quando duas festas caem no mesmo dia."),
            ("Como ficam o contrato e o sinal?", "Proposta por link e contrato que fecha o negócio e abre o financeiro; o sinal via Pix tem baixa sozinha."),
        ],
    },
    {
        "id": "estandes",
        "slug": "sistema-para-venda-de-stands",
        "nome": "Stand de vendas",
        "titulo": "Sistema para venda de stands em feiras, com mapa e IA | Zaq",
        "h1": "Sistema para venda de stands, do mapa ao stand quitado",
        "descricao": "Para feira, outlet, bazar e evento com stands: mapa público com pré-reserva, funil do lojista que anda sozinho, contrato por empresa, sinal via Pix e custo por stand vendido.",
        "abertura": "Feira, outlet, bazar e evento com stands para lojista: mapa público da edição com pré-reserva, funil do lojista que anda sozinho e o custo de cada stand vendido a partir do anúncio.",
        "msg": "Oi! Vendo stands em feira e quero um orçamento do Zaq",
        "perguntas": [
            ("O lojista escolhe o stand sozinho?", "Escolhe. No mapa público da edição o lojista escolhe o stand e faz a pré-reserva com vencimento; a gestão bloqueia o que não vende."),
            ("Dá para saber quanto custou cada stand vendido?", "Dá. Quem clica no anúncio e reserva pelo mapa cai no card certo, e você vê o custo por stand vendido."),
        ],
    },
    {
        "id": "led",
        "slug": "sistema-para-loja-de-iluminacao",
        "nome": "Iluminação e LED",
        "titulo": "Sistema para loja de iluminação e LED com IA | Zaq",
        "h1": "Sistema para loja de iluminação e LED, do balcão à obra",
        "descricao": "Para loja de iluminação, distribuidor de LED e projetos luminotécnicos: catálogo com ficha técnica, orçamento com aceite no celular, estoque por endereço, expedição e acompanhamento da obra.",
        "abertura": "Loja de iluminação, distribuidor de LED e projetos luminotécnicos: catálogo com ficha técnica, orçamento com aceite no celular, estoque por endereço, expedição e a sala do projeto para acompanhar a obra do cliente.",
        "msg": "Oi! Tenho uma loja de iluminação e LED e quero um orçamento do Zaq",
        "perguntas": [
            ("Dá para importar o catálogo?", "Dá: o catálogo entra pela planilha, com ficha técnica, marcas, NCM conferido e preço por lista de cliente."),
            ("O cliente aprova o orçamento pelo celular?", "Aprova. O orçamento tem aceite no celular, alçada de aprovação e desconto, e toda proposta vira card no funil da loja."),
        ],
    },
    {
        "id": "otica",
        "slug": "sistema-para-otica",
        "nome": "Ótica",
        "titulo": "Sistema para ótica com WhatsApp e IA | Zaq",
        "h1": "Sistema para ótica: receita, laboratório e entrega num lugar só",
        "descricao": "Para ótica de rua e rede com várias lojas: ordem de serviço com a receita, aviso de óculos prontos no WhatsApp, central que distribui o cliente e boletim de cada loja.",
        "abertura": "Ótica de rua ou rede com central e várias lojas: ordem de serviço com o grau da receita, mensagens que saem sozinhas quando os óculos ficam prontos e um boletim de cada loja.",
        "msg": "Oi! Tenho uma ótica e quero um orçamento do Zaq",
        "perguntas": [
            ("Avisa o cliente quando os óculos ficam prontos?", "Avisa sozinho, e também lembra quem não buscou, a receita que faz um ano e a lente de contato acabando."),
            ("Funciona para rede com várias lojas?", "Funciona: a central leva o cliente para a loja certa, o vendedor da loja atende e o supervisor é avisado."),
        ],
    },
    {
        "id": "suplementos",
        "slug": "sistema-para-loja-de-suplementos",
        "nome": "Suplementos e cozinha fit",
        "titulo": "Sistema para loja de suplementos e marmitaria fit | Zaq",
        "h1": "Sistema para loja de suplementos e cozinha fit",
        "descricao": "Para loja de suplementos, marmitaria fit, confeitaria e padaria: custo de cada prato pela ficha técnica, curva ABC, venda no balcão e pelo WhatsApp com entrega, caixa e estoque.",
        "abertura": "Loja de suplementos, marmitaria fit, confeitaria e padaria: a prateleira e a cozinha na mesma conta, com o custo de cada prato, curva ABC e venda no balcão e pelo WhatsApp.",
        "msg": "Oi! Tenho uma loja de suplementos e quero um orçamento do Zaq",
        "perguntas": [
            ("Calcula o custo de cada marmita?", "Calcula pela ficha técnica; a produção do dia baixa os insumos, sobe o prato pronto e imprime a etiqueta."),
            ("Vende pelo WhatsApp com entrega?", "Vende: no balcão e pelo WhatsApp, com entrega, saindo do lugar certo do estoque."),
        ],
    },
    {
        "id": "hortifruti",
        "slug": "sistema-para-hortifruti",
        "nome": "Hortifrúti e CEASA",
        "titulo": "Sistema para hortifrúti, cestas e compra no CEASA | Zaq",
        "h1": "Sistema para hortifrúti, do pedido da semana ao CEASA",
        "descricao": "Para fornecedor de cestas, sacolão e distribuidor que compra no CEASA: pedidos pelo WhatsApp, compra somada dos pedidos, romaneio da rota e financeiro da semana sem planilha.",
        "abertura": "Fornecedor de cestas, sacolão e distribuidor que compra no CEASA: pedidos da semana pelo WhatsApp, compra somada dos pedidos, romaneio da rota para o motorista e o financeiro da semana sem planilha.",
        "msg": "Oi! Trabalho com hortifrúti e quero um orçamento do Zaq",
        "perguntas": [
            ("Ele soma o que comprar no CEASA?", "Soma: a compra sai dos pedidos, dizendo quanto de cada item comprar na quarta para entregar na quinta."),
            ("O motorista recebe a rota?", "Recebe o romaneio da rota; a nota do fornecedor é conferida e o estoque fica com o que chegou de verdade."),
        ],
    },
    {
        "id": "obras",
        "slug": "sistema-para-construtora",
        "nome": "Construção e reforma",
        "titulo": "Sistema para construtora e obras, com app do mestre | Zaq",
        "h1": "Sistema para construtora: o canteiro no celular do mestre",
        "descricao": "Para construtora, loteamento, reforma e engenharia: app do mestre pelo WhatsApp sem senha, nota que vira material contado, mapa 3D das casas e suprimentos com cotação e pedido.",
        "abertura": "Construtora, loteamento, reforma e engenharia: o mestre registra a etapa pelo WhatsApp, sem senha; a nota vira material contado e o mapa 3D mostra cada casa crescendo e qual gasta acima das irmãs.",
        "msg": "Oi! Trabalho com construção e quero um orçamento do Zaq",
        "perguntas": [
            ("O mestre de obras precisa de senha?", "Não. O app do mestre entra pelo WhatsApp: foto da etapa, etapa feita e material usado, sem nenhum valor na tela dele."),
            ("Controla o material da obra?", "Controla: a nota vira material contado, a baixa é registrada por casa e o almoxarifado avisa o mínimo."),
        ],
    },
    {
        "id": "seguros",
        "slug": "sistema-para-corretora-de-seguros",
        "nome": "Corretora de seguros",
        "titulo": "Sistema para corretora de seguros com IA no WhatsApp | Zaq",
        "h1": "Sistema para corretora de seguros que avisa a renovação",
        "descricao": "Para corretora de auto, frota, vida, residencial, empresarial e saúde: aviso de renovação 60, 30 e 15 dias antes, funil de cotação, comissão a receber da seguradora e IA no primeiro contato.",
        "abertura": "Auto, frota, vida, residencial, empresarial e saúde: carteira de apólices que avisa o corretor antes do fim da vigência, funil de cotação e um financeiro que entende que a comissão vem da seguradora.",
        "msg": "Oi! Tenho uma corretora de seguros e quero um orçamento do Zaq",
        "perguntas": [
            ("Avisa a renovação das apólices?", "Avisa no celular do corretor 60, 30 e 15 dias antes do fim da vigência, com prêmio, comissão estimada e classe de bônus."),
            ("A IA atende o lead do anúncio?", "Atende: o lead chega no WhatsApp ligado ao anúncio, a IA faz o primeiro contato e passa para o corretor."),
        ],
    },
    {
        "id": "servicos",
        "slug": "sistema-para-empresa-de-servicos",
        "nome": "Serviços e consultoria",
        "titulo": "CRM com IA para consultoria, agência e empresa de serviços | Zaq",
        "h1": "CRM com IA para empresa de serviços e consultoria",
        "descricao": "Para consultoria, agência, contabilidade, advocacia, software e educação: lead PJ com segmento e porte, reunião na agenda, proposta aprovada por link e contrato assinado pelo celular.",
        "abertura": "Consultoria, agência, contabilidade, advocacia, software e educação: lead PJ com segmento e porte, reunião na agenda, proposta aprovada por link e contrato de prestação de serviços assinado pelo celular.",
        "msg": "Oi! Tenho uma empresa de serviços e quero um orçamento do Zaq",
        "perguntas": [
            ("O cliente aprova a proposta por link?", "Aprova: a proposta tem cara de documento, cada serviço com o que inclui, e o cliente aprova pelo link."),
            ("Tem contrato assinado pelo celular?", "Tem. O contrato de prestação de serviços é assinado pelo celular, e a venda só conta com o contrato assinado."),
        ],
    },
]

# O que a IA faz, com as palavras da home (seções "A máquina de vendas").
IA_ITENS = [
    ("Atende o primeiro contato", "A IA atende no seu WhatsApp, entende o que a pessoa quer, qualifica, marca a visita ou a reunião conferindo a agenda e passa para o vendedor certo. Fora do horário, ela responde."),
    ("Resgata o lead que esfriou", "O Resgate da IA volta a chamar quem parou de responder, com três toques e um supervisor acompanhando."),
    ("Ajuda quem atende", "Ao lado de cada conversa, resposta sugerida, resumo e próximo passo."),
    ("Move o funil sozinha", "O card lê a conversa e anda sozinho quando o cliente responde ao preço."),
    ("Liga a venda ao anúncio", "Cada lead chega ligado ao anúncio que o trouxe, cada anúncio recebe nota pelo que aconteceu depois do clique, e o Zaq devolve para a Meta quem comprou de verdade."),
    ("Faz o vídeo do lançamento", "No Studio, a peça e o vídeo vertical para Reels com IA, publicados no Instagram e no Facebook. A Marca diz o que a IA pode e não pode falar da sua empresa."),
]

PERGUNTAS_GERAIS = [
    ("Quanto custa o Zaq?", "Não existe plano de prateleira. Você conta o que precisa pelo WhatsApp e recebe um valor para o seu caso, com o que entra e o que fica de fora, por escrito, no modelo de setup mais mensalidade."),
    ("Preciso estar em Teresina para usar?", "Não. O Zaq é feito em Teresina (PI), mas funciona pela internet, no painel e no WhatsApp, para empresa de qualquer cidade."),
]

PAGINA_IA = {
    "slug": "ia-no-whatsapp-para-empresas",
    "titulo": "Ferramenta de IA no WhatsApp para empresas | Zaq",
    "h1": "IA no WhatsApp para empresas: atende, qualifica e marca",
    "descricao": "O Zaq coloca IA no WhatsApp da sua empresa: atende o primeiro contato, qualifica, marca na agenda, resgata o lead que esfriou e liga cada venda ao anúncio. Feito em Teresina (PI) para todo o Brasil.",
    "abertura": "Ferramenta de IA boa é a que trabalha onde o seu cliente já está. No Zaq, a IA atende no WhatsApp da sua empresa, conversa com as palavras do seu ramo e entrega o cliente pronto para o vendedor, com tudo registrado no funil.",
    "perguntas": [
        ("A IA substitui o atendente?", "Não. Ela faz o primeiro contato, qualifica e passa para o vendedor certo; quem atende ganha resposta sugerida, resumo e próximo passo ao lado de cada conversa."),
        ("A IA responde fora do horário?", "Responde, e o lead que esfriou volta pelo Resgate da IA, com três toques e um supervisor acompanhando."),
    ],
}

PAGINA_TERESINA = {
    "slug": "ia-para-empresas-em-teresina",
    "titulo": "IA para empresas em Teresina (PI): WhatsApp, vendas e gestão | Zaq",
    "h1": "IA para empresas em Teresina, feita em Teresina",
    "descricao": "O Zaq é um sistema com IA no WhatsApp feito em Teresina, Piauí: atendimento, funil de vendas, agenda e financeiro com as palavras do seu ramo. Clínica, ótica, buffet, construção, seguros e mais.",
    "abertura": "O Zaq nasceu em Teresina, no Piauí, para o comércio e os serviços que vivem do WhatsApp. A IA atende o primeiro contato da sua empresa, e o painel junta atendimento, vendas, agenda e financeiro com as palavras do seu ramo.",
    "perguntas": [
        ("O Zaq atende empresas fora de Teresina?", "Atende. O Zaq funciona pela internet, no painel e no WhatsApp, para empresa de qualquer cidade."),
        ("Tem gente de verdade do outro lado?", "Tem. A conversa para montar o Zaq acontece no WhatsApp mesmo, com gente de verdade, e a equipe entra por link, sem senha."),
    ],
}


# ---------------------------------------------------------------------------
# Leitura da home
# ---------------------------------------------------------------------------
def ler_ramos_da_home() -> dict[str, dict]:
    texto = (RAIZ / "index.html").read_text(encoding="utf-8")
    achados = {}
    for m in re.finditer(r'<article class="ramo" id="ramo-(\w+)".*?</article>', texto, re.S):
        bloco = m.group(0)
        quem = re.search(r'<div class="quem">(.*?)</div>', bloco, re.S)
        frase = re.search(r'<p class="frase">(.*?)</p>', bloco, re.S)
        lista = re.search(r"<ul>(.*?)</ul>", bloco, re.S)
        img = re.search(r'<img src="([^"]+)" alt="([^"]*)"', bloco)
        if not (quem and frase and lista and img):
            raise SystemExit(f"ramo {m.group(1)}: a home mudou de formato; ajuste o gerador")
        itens = re.findall(r"<li>(.*?)</li>", lista.group(1), re.S)
        achados[m.group(1)] = {
            "quem": quem.group(1).strip(),
            "frase": frase.group(1).strip(),
            "itens": [i.strip() for i in itens],
            "img": img.group(1),
            "img_alt": img.group(2),
        }
    return achados


def ler_numeros_da_home() -> tuple[list[tuple[str, str]], str]:
    texto = (RAIZ / "index.html").read_text(encoding="utf-8")
    sec = re.search(r'<section class="numeros".*?</section>', texto, re.S)
    if not sec:
        raise SystemExit("a home não tem mais a seção de números; ajuste o gerador")
    nums = re.findall(r'<div class="v">(.*?)</div><div class="l">(.*?)</div>', sec.group(0), re.S)
    nota = re.search(r'<p class="num-nota">(.*?)</p>', sec.group(0), re.S)
    return nums, (nota.group(1).strip() if nota else "")


# ---------------------------------------------------------------------------
# Montagem
# ---------------------------------------------------------------------------
def e(t: str) -> str:
    return html.escape(t, quote=True)


def sem_tags(t: str) -> str:
    # "125<small>mil</small>" vira "125 mil", não "125mil".
    t = re.sub(r"<small>", " ", t)
    return re.sub(r"<[^>]+>", "", t).strip()


def link_whats(msg: str) -> str:
    return f"https://wa.me/{WHATS}?text={quote(msg)}"


CSS = """
:root{--bg:#0A0F0C;--surface:#121A16;--line:#1E2A23;--neon:#25D366;--neon-bright:#46F58A;--neon-borda:#1E4A3A;--neon-fundo:#10241A;
--text:#EAF2ED;--text-dim:#8FA197;--text-faint:#5E6F66;--display:"Bricolage Grotesque",system-ui,sans-serif;--body:"Inter",system-ui,sans-serif;--mono:"JetBrains Mono",ui-monospace,monospace}
*{box-sizing:border-box;margin:0;padding:0}
body{background:var(--bg);color:var(--text);font-family:var(--body);line-height:1.55;-webkit-font-smoothing:antialiased;overflow-x:hidden}
a{color:inherit}
.wrap{width:100%;max-width:820px;margin:0 auto;padding:0 20px}
.glow{position:fixed;top:-30%;left:50%;transform:translateX(-50%);width:140%;height:70vh;pointer-events:none;z-index:0;background:radial-gradient(ellipse at center,rgba(37,211,102,.14),transparent 60%);filter:blur(20px)}
nav{position:sticky;top:0;z-index:50;backdrop-filter:blur(12px);background:rgba(10,15,12,.78);border-bottom:1px solid var(--line)}
.nav-in{display:flex;align-items:center;justify-content:space-between;height:62px;gap:10px}
.logo{display:flex;align-items:center;gap:10px;font-family:var(--display);font-weight:800;font-size:22px;letter-spacing:-.02em;text-decoration:none}
.logo .mark{width:32px;height:32px;border-radius:9px;background:linear-gradient(145deg,var(--neon),#0FA85A);color:#04150C;display:grid;place-items:center;font-weight:800;font-size:19px}
.nav-cta{font-size:14px;font-weight:700;padding:9px 16px;border-radius:999px;background:var(--neon);color:#04150C;text-decoration:none;white-space:nowrap}
.nav-cta:hover{background:var(--neon-bright)}
.trilha{font-size:13px;color:var(--text-faint);margin-top:26px}
.trilha a{color:var(--text-dim)}
header,main,footer{position:relative;z-index:1}
header{padding:14px 0 6px}
.eyebrow{font-family:var(--mono);font-size:12px;letter-spacing:.16em;text-transform:uppercase;color:var(--neon);margin-top:18px}
h1{font-family:var(--display);font-weight:800;font-size:clamp(2rem,7vw,3rem);line-height:1.04;letter-spacing:-.03em;margin-top:10px;text-wrap:balance}
.sub{font-size:1.08rem;color:var(--text-dim);margin-top:16px;max-width:60ch}
.cta{display:inline-flex;align-items:center;gap:8px;margin-top:22px;font-weight:700;padding:13px 22px;border-radius:999px;background:var(--neon);color:#04150C;text-decoration:none}
.cta:hover{background:var(--neon-bright)}
section{padding:34px 0 6px}
h2{font-family:var(--display);font-weight:800;font-size:clamp(1.4rem,4.5vw,1.9rem);letter-spacing:-.02em;line-height:1.15}
h3{font-family:var(--display);font-weight:700;font-size:1.08rem;margin-top:16px}
p{margin-top:10px}
.dim{color:var(--text-dim)}
ul.lista{list-style:none;margin-top:14px;display:grid;gap:12px}
ul.lista li{background:var(--surface);border:1px solid var(--line);border-radius:14px;padding:14px 16px;color:var(--text-dim)}
ul.lista li b{color:var(--text)}
figure{margin-top:18px}
figure img{width:100%;height:auto;border-radius:14px;border:1px solid var(--line);display:block}
figcaption{font-size:13px;color:var(--text-faint);margin-top:8px}
.ia{display:grid;gap:12px;margin-top:14px}
@media(min-width:680px){.ia{grid-template-columns:1fr 1fr}}
.ia div{border:1px solid var(--neon-borda);background:var(--neon-fundo);border-radius:14px;padding:14px 16px}
.ia h3{margin-top:0}
.ia p{color:var(--text-dim);font-size:.95rem;margin-top:6px}
.nums{display:grid;grid-template-columns:repeat(auto-fit,minmax(140px,1fr));gap:10px;margin-top:14px}
.nums div{background:var(--surface);border:1px solid var(--line);border-radius:14px;padding:12px 14px}
.nums b{font-family:var(--display);font-size:1.6rem;display:block}
.nums span{font-size:.86rem;color:var(--text-dim)}
.nota{font-size:12px;color:var(--text-faint);margin-top:8px}
details{border-bottom:1px solid var(--line);padding:14px 0}
summary{cursor:pointer;font-weight:600;list-style-position:outside}
details p{color:var(--text-dim)}
.ramos{display:flex;flex-wrap:wrap;gap:8px;margin-top:14px}
.ramos a{font-size:.9rem;padding:8px 14px;border-radius:999px;border:1px solid var(--line);color:var(--text-dim);text-decoration:none}
.ramos a:hover{border-color:var(--neon);color:var(--text)}
.fecha{margin:40px 0 50px;border:1px solid var(--neon-borda);background:var(--neon-fundo);border-radius:18px;padding:24px}
footer{border-top:1px solid var(--line);padding:30px 0;text-align:center}
footer p{color:var(--text-faint);font-size:13px;margin-top:6px}
footer a{color:var(--text-dim)}
a:focus-visible,summary:focus-visible{outline:2px solid var(--neon);outline-offset:3px}
"""

FONTES = (
    '<link rel="preconnect" href="https://fonts.googleapis.com">\n'
    '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>\n'
    '<link href="https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:opsz,wght@12..96,700;12..96,800&family=Inter:wght@400;500;600&family=JetBrains+Mono:wght@500&display=swap" rel="stylesheet">'
)


def json_ld(obj) -> str:
    # Escapa "</" pra nenhum texto fechar o <script> antes da hora.
    corpo = json.dumps(obj, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    return f'<script type="application/ld+json">{corpo}</script>'


def schema_pagina(slug: str, nome_trilha: str, perguntas) -> str:
    url = f"{SITE}/{slug}.html"
    grafo = {
        "@context": "https://schema.org",
        "@graph": [
            {
                "@type": "BreadcrumbList",
                "itemListElement": [
                    {"@type": "ListItem", "position": 1, "name": "Zaq", "item": SITE},
                    {"@type": "ListItem", "position": 2, "name": nome_trilha, "item": url},
                ],
            },
            {
                "@type": "FAQPage",
                "mainEntity": [
                    {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": r}}
                    for q, r in perguntas
                ],
            },
        ],
    }
    return json_ld(grafo)


def bloco_perguntas(perguntas) -> str:
    itens = "\n".join(
        f"<details><summary>{e(q)}</summary><p>{e(r)}</p></details>" for q, r in perguntas
    )
    return f'<section id="perguntas"><h2>Perguntas frequentes</h2>\n{itens}\n</section>'


def bloco_ia() -> str:
    itens = "\n".join(f"<div><h3>{e(t)}</h3><p>{e(d)}</p></div>" for t, d in IA_ITENS)
    return f'<section id="ia"><h2>Onde a IA trabalha por você</h2>\n<div class="ia">\n{itens}\n</div>\n<p class="dim">Mais detalhes em <a href="/{PAGINA_IA["slug"]}.html">IA no WhatsApp para empresas</a>.</p></section>'


def bloco_numeros() -> str:
    nums, nota = ler_numeros_da_home()
    cartoes = "\n".join(f"<div><b>{sem_tags(v)}</b><span>{sem_tags(l)}</span></div>" for v, l in nums)
    return f'<section id="numeros"><h2>O Zaq hoje</h2>\n<div class="nums">\n{cartoes}\n</div>\n<p class="nota">{e(nota)}</p></section>'


def bloco_ramos(exceto: str | None = None) -> str:
    links = "\n".join(
        f'<a href="/{r["slug"]}.html">{e(r["nome"])}</a>' for r in RAMOS if r["id"] != exceto
    )
    return f'<section id="ramos"><h2>O Zaq em outros ramos</h2>\n<div class="ramos">\n{links}\n</div></section>'


def pagina(*, slug, titulo, descricao, eyebrow, h1, abertura, corpo, perguntas, msg, nome_trilha) -> str:
    url = f"{SITE}/{slug}.html"
    zap = link_whats(msg)
    return f"""<!doctype html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{e(titulo)}</title>
<meta name="description" content="{e(descricao)}">
<link rel="canonical" href="{url}">
<meta property="og:title" content="{e(titulo)}">
<meta property="og:description" content="{e(descricao)}">
<meta property="og:type" content="website">
<meta property="og:url" content="{url}">
<meta property="og:image" content="{SITE}/og.png">
<meta property="og:locale" content="pt_BR">
<meta name="twitter:card" content="summary_large_image">
<link rel="icon" href="/favicon.svg" type="image/svg+xml">
{FONTES}
{schema_pagina(slug, nome_trilha, perguntas)}
<style>{CSS}</style>
</head>
<body>
<!-- Gerado por ferramentas/gerar_paginas_seo.py: edite lá, não aqui. -->
<div class="glow" aria-hidden="true"></div>
<nav><div class="wrap nav-in"><a class="logo" href="/"><span class="mark">Z</span>Zaq</a><a class="nav-cta" href="{e(zap)}" target="_blank" rel="noopener">Pedir orçamento</a></div></nav>
<header><div class="wrap">
<p class="trilha"><a href="/">Zaq</a> › {e(nome_trilha)}</p>
<p class="eyebrow">{e(eyebrow)}</p>
<h1>{e(h1)}</h1>
<p class="sub">{e(abertura)}</p>
<a class="cta" href="{e(zap)}" target="_blank" rel="noopener">Pedir orçamento no WhatsApp →</a>
</div></header>
<main><div class="wrap">
{corpo}
{bloco_perguntas(perguntas)}
<div class="fecha"><h2>Me conta o seu ramo.</h2><p class="dim">Uma mensagem no WhatsApp e a gente te mostra o Zaq falando a sua língua. Cada negócio é um orçamento, por escrito.</p><a class="cta" href="{e(zap)}" target="_blank" rel="noopener">Falar no WhatsApp →</a></div>
</div></main>
<footer><div class="wrap"><p><b>Zaq</b> · sistema com IA no WhatsApp · feito em Teresina, Piauí 🇧🇷</p><p><a href="/">início</a> · <a href="/{PAGINA_IA["slug"]}.html">IA no WhatsApp</a> · <a href="/{PAGINA_TERESINA["slug"]}.html">Teresina</a> · <a href="/atualizacoes.html">o que mudou</a> · <a href="/seja-parceiro.html">seja parceiro</a> · <a href="https://app.zaq-ia.com/login">entrar</a></p></div></footer>
</body>
</html>
"""


def pagina_ramo(r: dict, home: dict) -> str:
    dados = home[r["id"]]
    itens = "\n".join(f"<li>{i}</li>" for i in dados["itens"])  # já é HTML revisado da home
    corpo = f"""<section id="recursos"><h2>O que o Zaq faz para {e(r["nome"].lower())}</h2>
<p class="dim">{e(sem_tags(dados["frase"]))} Para {e(sem_tags(dados["quem"]))}.</p>
<ul class="lista">
{itens}
</ul>
<figure><img src="{e(dados["img"])}" alt="{e(dados["img_alt"])}" width="960" height="597" loading="lazy"><figcaption>{e(dados["img_alt"])}</figcaption></figure>
</section>
{bloco_ia()}
{bloco_numeros()}
{bloco_ramos(exceto=r["id"])}"""
    return pagina(
        slug=r["slug"], titulo=r["titulo"], descricao=r["descricao"], eyebrow=f"Zaq para {r['nome'].lower()}",
        h1=r["h1"], abertura=r["abertura"], corpo=corpo, perguntas=r["perguntas"] + PERGUNTAS_GERAIS,
        msg=r["msg"], nome_trilha=r["nome"],
    )


def pagina_ia() -> str:
    p = PAGINA_IA
    itens = "\n".join(f"<li><b>{e(t)}.</b> {e(d)}</li>" for t, d in IA_ITENS)
    corpo = f"""<section id="o-que-faz"><h2>O que a IA do Zaq faz</h2>
<ul class="lista">
{itens}
</ul></section>
<section id="por-ramo"><h2>A mesma IA, com as palavras do seu ramo</h2>
<p class="dim">Clínica não tem “festa”, buffet não tem “paciente”, ótica não tem “lote”. Cada ramo tem as suas telas, as suas palavras e os seus números.</p>
<div class="ramos">
{chr(10).join(f'<a href="/{r["slug"]}.html">{e(r["nome"])}</a>' for r in RAMOS)}
</div></section>
{bloco_numeros()}"""
    return pagina(
        slug=p["slug"], titulo=p["titulo"], descricao=p["descricao"], eyebrow="Ferramenta de IA para empresas",
        h1=p["h1"], abertura=p["abertura"], corpo=corpo, perguntas=p["perguntas"] + PERGUNTAS_GERAIS,
        msg="Oi! Quero conhecer a IA do Zaq pra minha empresa", nome_trilha="IA no WhatsApp",
    )


def pagina_teresina() -> str:
    p = PAGINA_TERESINA
    corpo = f"""<section id="ramos-teresina"><h2>Para cada ramo, a sua página</h2>
<p class="dim">Escolha o seu ramo para ver o que o Zaq faz nele.</p>
<div class="ramos">
{chr(10).join(f'<a href="/{r["slug"]}.html">{e(r["nome"])}</a>' for r in RAMOS)}
</div></section>
{bloco_ia()}
{bloco_numeros()}
<section id="comeca"><h2>Três conversas. Nenhum formulário.</h2>
<ul class="lista">
<li><b>Você conta o seu ramo.</b> No WhatsApp mesmo: o que vende, quantas pessoas, como o cliente chega hoje.</li>
<li><b>A gente monta o Zaq para você.</b> Com as palavras do seu ramo, os seus números e o seu WhatsApp conectado.</li>
<li><b>Você acompanha de onde estiver.</b> O painel na mesa, o app no bolso, e o Zaq te avisando do que importa.</li>
</ul></section>"""
    perguntas = p["perguntas"] + [PERGUNTAS_GERAIS[0]]
    return pagina(
        slug=p["slug"], titulo=p["titulo"], descricao=p["descricao"], eyebrow="Teresina · Piauí",
        h1=p["h1"], abertura=p["abertura"], corpo=corpo, perguntas=perguntas,
        msg="Oi! Sou de Teresina e quero um orçamento do Zaq", nome_trilha="Teresina",
    )


def sitemap(paginas: list[str]) -> str:
    urls = [f"{SITE}/"] + [f"{SITE}/{s}.html" for s in paginas] + [
        f"{SITE}/atualizacoes.html",
        f"{SITE}/seja-parceiro.html",
    ]
    corpo = "\n".join(f"  <url><loc>{u}</loc><lastmod>{HOJE}</lastmod></url>" for u in urls)
    return f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n{corpo}\n</urlset>\n'


def llms_txt() -> str:
    nums, nota = ler_numeros_da_home()
    linhas_nums = "\n".join(f"- {sem_tags(v)}: {sem_tags(l)}" for v, l in nums)
    ramos = "\n".join(f"- [{r['nome']}]({SITE}/{r['slug']}.html): {r['descricao']}" for r in RAMOS)
    return f"""# Zaq

> Sistema com IA no WhatsApp para empresas, feito em Teresina, Piauí, Brasil. Junta atendimento, funil de vendas (CRM), agenda, equipe e financeiro, com as telas e as palavras de cada ramo. A IA atende o primeiro contato no WhatsApp, qualifica, marca na agenda e passa para o vendedor.

Preço sob orçamento (setup mais mensalidade), sem plano de prateleira. Contato pelo WhatsApp: https://wa.me/{WHATS}

## Páginas principais

- [Início]({SITE}/)
- [IA no WhatsApp para empresas]({SITE}/{PAGINA_IA['slug']}.html)
- [IA para empresas em Teresina]({SITE}/{PAGINA_TERESINA['slug']}.html)
- [O que mudou no Zaq]({SITE}/atualizacoes.html)

## Ramos

{ramos}

## Números ({nota})

{linhas_nums}
"""


def main() -> None:
    home = ler_ramos_da_home()
    faltando = {r["id"] for r in RAMOS} - set(home)
    if faltando:
        raise SystemExit(f"ramos sem bloco na home: {sorted(faltando)}")
    gerados = []
    for r in RAMOS:
        (RAIZ / f"{r['slug']}.html").write_text(pagina_ramo(r, home), encoding="utf-8")
        gerados.append(r["slug"])
    (RAIZ / f"{PAGINA_IA['slug']}.html").write_text(pagina_ia(), encoding="utf-8")
    (RAIZ / f"{PAGINA_TERESINA['slug']}.html").write_text(pagina_teresina(), encoding="utf-8")
    gerados += [PAGINA_IA["slug"], PAGINA_TERESINA["slug"]]
    (RAIZ / "sitemap.xml").write_text(sitemap(gerados), encoding="utf-8")
    (RAIZ / "llms.txt").write_text(llms_txt(), encoding="utf-8")
    print(f"{len(gerados)} páginas, sitemap.xml e llms.txt gerados")


if __name__ == "__main__":
    main()
