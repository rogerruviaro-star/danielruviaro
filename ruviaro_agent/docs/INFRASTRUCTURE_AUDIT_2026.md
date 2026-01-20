# 🛡️ AUDITORIA DE INFRAESTRUTURA E SEGURANÇA (VPS)
**Data:** 2026-01-19
**Status:** Análise Inicial

Este documento registra os pontos de atenção levantados sobre o ambiente de produção (Hostinger VPS).

## 1. 🚨 PONTOS CRÍTICOS (AÇÃO IMEDIATA)

### A) Backups (Risco Extremo)
*   **Situação Atual:** "Ainda não há backups" configurados no painel.
*   **Risco:** Perda total de dados em caso de falha, invasão ou erro humano.
*   **Ação Necessária:** Ativar **Backup Diário Automático** no painel da Hostinger imediatamente.

### B) Segurança de Acesso (Risco Médio/Alto)
*   **Situação Atual:** Acesso via `root` com senha.
*   **Risco:** Brute-force attacks podem descobrir a senha. Uso de root aumenta impacto de erros.
*   **Recomendação:**
    1. Migrar para autenticação via **Chave SSH** (SSH Key).
    2. Desativar login por senha.
    3. (Futuro) Criar usuário comum (não-root) para rodar o agente.

---

## 2. ⚠️ PONTOS DE MELHORIA (MÉDIO PRAZO)

### A) Docker
*   **Situação Atual:** Docker instalado mas não utilizado. Agente roda via PM2 (Python direto).
*   **Oportunidade:** Containerizar a aplicação traria isolamento, facilidade de deploy e rollback.
*   **Plano:** Migrar `ruviaro_agent` para Docker no futuro.

### B) Credenciais e Secrets
*   **Situação Atual:** `.env` local.
*   **Recomendação:** Nunca commitar `.env` (já seguido). No futuro, usar Docker Secrets ou Vault se a complexidade aumentar.

---

## 3. ✅ PONTOS POSITIVOS
*   **SO:** Ubuntu 24.04 LTS (Moderno e seguro).
*   **Gerenciamento:** Uso de PM2 para processo (correto para MVP).

---

## 🏗️ ARQUITETURA IDEAL SUGERIDA (FUTURO)
1.  **Docker Compose:**
    *   Container 1: Aplicação (Python)
    *   Container 2: Redis (Memória Rápida/Cache) - *A implementar*
    *   Container 3: Banco Vetorial (ChromaDB/PGVector) - *A implementar*
2.  **Backup Strategy:** Snapshots diários + Dump do banco enviado para S3/Drive externo.
