# 🚀 MANUAL DE DEPLOY (ATUALIZAÇÃO DO SERVIDOR)

Salve este arquivo para referência futura.

## 1️⃣ NO SEU COMPUTADOR (Gatilho)
Abra o terminal na pasta do projeto (`c:\Users\Speed\iaruviaro\danielruviaro`) e execute:

```powershell
git add .
git commit -m "Nova atualizacao manualmente"
git push
```
*(Aguarde aparecer "Everything up-to-date" ou ver o upload acontecer)*

---

## 2️⃣ NO SERVIDOR VPS (Atualização Real)
Acesse o servidor e puxe a atualização:

```bash
# 1. Conectar (Se pedir senha, digite a senha do root)
ssh root@76.13.70.207

# 2. Ir para a pasta do robô
cd /var/www/ruviaro-agent

# 3. Baixar o código novo do GitHub
git pull

# 4. Reiniciar o Daniel para aplicar as mudanças
pm2 restart ruviaro-agent

# 5. (Opcional) Ver se está tudo bem
pm2 log
```

**DICA:** Se o `git pull` der erro, geralmente um `git reset --hard` resolve (mas apaga mudanças locais no servidor, o que é seguro se você só edita no PC).
