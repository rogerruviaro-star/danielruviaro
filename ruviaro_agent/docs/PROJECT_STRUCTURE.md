# 🧱 ESTRUTURA FÍSICA NO ANTIGRAVITY

**Projeto: Daniel – Auto Peças Ruviaro**

## VISÃO GERAL (ÁRVORE DE PASTAS)

Esta estrutura define a organização do "Cérebro" do Daniel. O código Python carregará estes arquivos em ordem para montar o System Prompt final.

```
ruviaro_agent/
└── brain/
    ├── 00_REGRAS_ABSOLUTAS/         # [PRIORIDADE MÁXIMA]
    │   ├── 00_01_IDENTIDADE_DO_DANIEL.md
    │   ├── 00_02_REGRA_DO_PONTO_VERDE.md
    │   ├── 00_03_REGRA_DO_SILENCIO.md
    │   ├── 00_04_REGRA_DE_EMOJIS.md
    │   ├── 00_05_REGRA_NAO_NARRAR_PROCESSO.md
    │   └── 00_06_REGRA_FORA_DE_HORARIO.md
    │
    ├── 01_PROCESSO_TECNICO/         # [ESPINHA DORSAL]
    │   ├── 01_01_TRIAGEM_INICIAL.md
    │   ├── 01_02_MECANICA_EXIGE_PLACA.md
    │   ├── 01_03_LATARIA_EXIGE_FOTO.md
    │   ├── 01_04_REGRA_ANTI_PRESSAO.md
    │   └── 01_05_QUANDO_PASSAR_PARA_HUMANO.md
    │
    ├── 02_CONHECIMENTO_FIXO/        # [COFRE]
    │   ├── 02_01_DADOS_DA_EMPRESA.md
    │   ├── 02_02_HORARIO_FUNCIONAMENTO.md
    │   ├── 02_03_PRECOS_BASICOS_FIXOS.md
    │   ├── 02_04_REGRAS_DE_PAGAMENTO.md
    │   └── 02_05_ENDERECO_E_LOCALIZACAO.md
    │
    ├── 03_CONTEUDO_VISUAL_E_LINKS/  # [SUPORTE]
    │   ├── 03_01_FOTOS_PADRAO_PASTILHA.md
    │   ├── 03_02_FOTOS_PADRAO_FILTROS.md
    │   ├── 03_03_FOTOS_PADRAO_CORREIAS.md
    │   ├── 03_04_LINK_CATALOGO.md
    │   └── 03_05_LINK_LOCALIZACAO.md
    │
    ├── 04_CONHECIMENTO_DINAMICO/    # [APRENDIZADO CONTROLADO]
    │   ├── 04_01_PERGUNTAS_FREQUENTES.md
    │   ├── 04_02_TERMOS_USADOS_POR_CLIENTES.md
    │   ├── 04_03_ERROS_COMUNS_DE_DEVOLUCAO.md
    │   └── 04_04_CAMINHOS_RAPIDOS_DE_TRIAGEM.md
    │
    ├── 05_FLUXOS_OPERACIONAIS/      # [SCRIPTS]
    │   ├── 05_01_FLUXO_PADRAO.md
    │   ├── 05_02_FLUXO_URGENCIA.md
    │   ├── 05_03_FLUXO_POS_PAGAMENTO.md
    │   ├── 05_04_FLUXO_POS_VENDA_STATUS.md
    │   └── 05_05_FLUXO_ENTREGA_RETIRADA.md
    │
    ├── 06_ESTILO_E_LINGUAGEM/       # [AJUSTE FINO]
    │   ├── 06_01_TOM_ADULTO.md
    │   ├── 06_02_FRASES_CURTAS.md
    │   └── 06_03_SEM_SIM_PATIA_FORCADA.md
    │
    └── 99_TESTES_E_AUDITORIA/       # [CONTROLE]
        ├── 99_01_TESTES_DE_ESTRESSE.md
        ├── 99_02_CASOS_REAIS_ERRADOS.md
        └── 99_03_CHECKLIST_DE_AUDITORIA.md
```

## 🔁 ORDEM DE EXECUÇÃO (PIPELINE)

1. **System Prompt Loader**: O script Python deverá iterar sobre essas pastas em ordem numérica (00 a 06).
2. **Concatenation**: Os arquivos `.md` serão lidos e concatenados para formar o System Prompt final enviado à OpenAI.
3. **Priority**: Regras em `00` aparecem primeiro no prompt, estabelecendo as diretrizes primárias que o LLM seguirá.

---

## 📌 MAPEAMENTO DE PRIORIDADE

| Pasta | Prioridade | Descrição |
|-------|------------|-----------|
| `00_REGRAS_ABSOLUTAS` | **MAXIMA** | Travas de segurança e comportamento inegociável. |
| `01_PROCESSO_TECNICO` | ALTA | O " algoritmo" de atendimento. |
| `02_CONHECIMENTO_FIXO` | MÉDIA | Dados estáticos que dispensam consulta. |
| `03_CONTEUDO_VISUAL` | MÉDIA | Links e imagens de apoio. |
| `04_CONHECIMENTO_DINAMICO` | BAIXA | Memória e aprendizado. |
| `05_FLUXOS_OPERACIONAIS` | BAIXA | Scripts de condução. |
| `06_ESTILO_E_LINGUAGEM` | NULA | Apenas formatação de texto. |

---

## IMPLEMENTAÇÃO

A pasta `ruviaro_agent/brain/` será a nova "Soul" do projeto.
O arquivo `system_persona.md` antigo será depreciado e seu conteúdo distribuído nestes arquivos.
