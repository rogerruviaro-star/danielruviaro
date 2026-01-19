@echo off
echo ==============================================
echo   ENVIANDO CODIGO PARA O GITHUB
echo ==============================================

echo [1/3] Adicionando arquivos...
git add .

echo.
echo [2/3] Commitando mudancas...
git commit -m "feat: agent 5-layer architecture and strict handoff fix"

echo.
echo [3/3] Enviando para o repositorio (Push)...
git push origin main

echo.
echo ==============================================
echo CODIGO SALVO NO GITHUB!
echo ==============================================
pause
